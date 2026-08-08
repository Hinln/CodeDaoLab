# -*- coding: utf-8 -*-
"""V0.2.5 稳定性测试。

覆盖：存档健壮性（损坏/路径穿越/旧档迁移/字段往返）、API 边界（空代码、
无 body、未知道具/任务）、心境与尝试次数钳制、秘境境界边界、沙箱补充。
"""

import json
import pathlib

from game import config, save
from game.player import Player


# ---------- 存档健壮性 ----------

def _save_dir() -> pathlib.Path:
    pth = pathlib.Path(config.SAVE_DIR)
    pth.mkdir(parents=True, exist_ok=True)
    return pth


def test_corrupt_save_returns_none(app):
    (_save_dir() / "broken.json").write_text("{not json", encoding="utf-8")
    assert save.load_game("broken") is None


def test_slot_path_traversal_sanitized(app):
    save.save_game(Player(name="穿越修士"), "../evil")
    # 不应越界写入上级目录
    assert not pathlib.Path(config.SAVE_DIR).joinpath("../evil.json").exists()
    # 槽位名被清洗为安全字符
    assert pathlib.Path(config.SAVE_DIR).joinpath("evil.json").exists()


def test_v1_save_auto_migration(app):
    v1 = {
        "version": 1,
        "player": {
            "name": "旧档修士",
            "realm_key": "qi1",
            "cultivation": 30,
            "completed_tasks": ["tutorial_run"],
        },
    }
    (_save_dir() / "old.json").write_text(json.dumps(v1, ensure_ascii=False), encoding="utf-8")
    p = save.load_game("old")
    assert p is not None
    assert p.name == "旧档修士"
    assert p.realm_key == "qi1"
    assert p.cultivation == 30
    # V0.2 新增字段自动补默认值
    assert p.comprehension == 10
    assert p.mindset == 100
    assert p.secret_log == {}
    assert p.achievements == []
    assert p.items == {}
    assert p.attempts == {}


def test_save_roundtrip_preserves_v02_fields(app):
    p = Player(name="往返修士")
    p.secret_log["qingyun"] = 2
    p.items["wudao_dan"] = 3
    p.achievements.append("secret_qingyun")
    p.attempts["tutorial_run"] = 5
    p.streak = 3
    p.techniques.append("print_huangji")
    p.branch_unlocked.append("branch_lingqi")
    save.save_game(p, "rt")
    p2 = save.load_game("rt")
    assert p2 is not None
    assert p2.name == "往返修士"
    assert p2.secret_log == {"qingyun": 2}
    assert p2.items == {"wudao_dan": 3}
    assert p2.achievements == ["secret_qingyun"]
    assert p2.attempts == {"tutorial_run": 5}
    assert p2.streak == 3
    assert p2.techniques == ["print_huangji"]
    assert p2.branch_unlocked == ["branch_lingqi"]


# ---------- API 边界 ----------

def test_empty_code_submit_not_crash(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/submit", json={"code": ""})
    assert resp.status_code == 200
    assert resp.get_json()["outcome"]["passed"] is False


def test_submit_without_body_not_crash(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/submit", data="")
    assert resp.status_code == 200
    assert resp.get_json()["outcome"]["passed"] is False


def test_empty_code_run_not_crash(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/run", json={"code": ""})
    assert resp.status_code == 200
    assert resp.get_json()["run"]["status"] in ("ok", "runtime")


def test_unknown_item_use_400(client, new_player):
    resp = client.post("/api/items/not_exist/use")
    assert resp.status_code == 400
    assert "不存在" in resp.get_json()["error"]


def test_unknown_task_submit_404(client, new_player):
    resp = client.post("/api/tasks/no_such_task/submit", json={"code": "print(1)"})
    assert resp.status_code == 404


# ---------- 心境与尝试次数钳制 ----------

def test_mindset_clamped_at_zero_after_many_failures(client, new_player):
    from game import server as server_mod

    for _ in range(60):
        client.post("/api/tasks/tutorial_run/submit", json={"code": "print('wrong')"})
    p = server_mod._current_player
    assert p.mindset == 0          # 钳制在 0，不跌为负
    assert p.streak == 0
    assert p.attempt_count("tutorial_run") == 60   # 只增不减


def test_success_recovers_mindset_and_streak(client, new_player):
    from game import server as server_mod

    for _ in range(60):
        client.post("/api/tasks/tutorial_run/submit", json={"code": "print('wrong')"})
    p = server_mod._current_player
    assert p.mindset == 0 and p.streak == 0

    resp = client.post("/api/tasks/tutorial_run/submit",
                       json={"code": "print('天地玄黄，宇宙洪荒。')"})
    data = resp.get_json()
    assert data["outcome"]["passed"] is True
    assert p.mindset == 2                       # 成功后心境 +2
    assert p.streak == 1
    assert p.attempt_count("tutorial_run") == 0 # 通过后清空失败记录


# ---------- 秘境边界 ----------

def test_secret_over_realm_forbidden(client, new_player):
    from game import server as server_mod

    p = server_mod._current_player
    p.secret_unlocked.append("qingyun")
    p.realm_key = "gold1"   # 已解锁但超出青云秘境上限（筑基）
    resp = client.post("/api/secret-realms/qingyun/enter")
    assert resp.status_code == 403


def test_secret_run_unknown_realm(client, new_player):
    # 未进入任何秘境时，运行未知秘境按“请先进入秘境”处理
    resp = client.post("/api/secret-realms/nope/run", json={"code": "print(1)"})
    assert resp.status_code == 400


# ---------- 沙箱补充 ----------

def test_sandbox_empty_code_ok():
    from game import sandbox

    r = sandbox.run_player_code("")
    assert r.status == "ok"
    assert r.is_ok
    assert r.stdout == ""


def test_sandbox_relative_traversal_blocked():
    from game import sandbox

    r = sandbox.run_player_code("open('../../CODEX.md').read()")
    assert r.status == "runtime"
    assert "禁止" in r.message
