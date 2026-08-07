# -*- coding: utf-8 -*-
"""V0.2 阶段六 · 秘境系统验收测试。

覆盖：三秘境数据定义、随机挑战可解性与随机性、门槛判定、首通/重复奖励、
秘境成就、API（总览/进入/运行/提交）、对话解锁。
"""

import random

import pytest

from game import achievements, curriculum, secret_realms
from game.player import Player

REALM_IDS = ["qingyun", "wanxiang", "tiangong"]


def _unlock_and_realm(player: Player, realm_id: str, realm_key: str):
    """将玩家解锁指定秘境并提升到指定境界。"""
    player.secret_unlocked.append(realm_id)
    player.realm_key = realm_key


# ---------- 数据定义 ----------

def test_three_realms_defined():
    realms = secret_realms.secret_realms()
    assert list(realms.keys()) == REALM_IDS
    for rid in REALM_IDS:
        r = realms[rid]
        assert r["name"]
        assert r["min_realm"] and curriculum.realm_order(r["min_realm"]) >= 0
        if r["max_realm"]:
            assert curriculum.realm_order(r["max_realm"]) >= curriculum.realm_order(r["min_realm"])
        assert r["templates"]
        for t in r["templates"]:
            assert t in secret_realms._GENERATORS, (rid, t)
        assert r["reward"].get("cultivation", 0) > 0


def test_realm_thresholds():
    realms = secret_realms.secret_realms()
    assert realms["qingyun"]["min_realm"] == "qi5" and realms["qingyun"]["max_realm"] == "foundation"
    assert realms["wanxiang"]["min_realm"] == "gold1" and realms["wanxiang"]["max_realm"] == "nas2"
    assert realms["tiangong"]["min_realm"] == "spr1" and realms["tiangong"]["max_realm"] is None


# ---------- 随机挑战生成 ----------

def test_generate_challenge_structure():
    for rid in REALM_IDS:
        task = secret_realms.generate_challenge(rid, random.Random(42))
        assert task["kind"] == "secret"
        assert task["no_solution"] is True
        # 内部保留参考答案供沙箱自检；对外 sanitize 时剔除
        assert task["solution"]
        assert task["secret_realm"] == rid
        assert task["story"] and task["starter_code"] and task["hints"]
        assert task["check"]["mode"] in ("output", "function")


def test_generated_challenge_is_solvable():
    """每个秘境随机生成的挑战，参考答案必须能通过沙箱验证。"""
    for rid in REALM_IDS:
        for seed in range(4):
            task = secret_realms.generate_challenge(rid, random.Random(seed * 101 + 7))
            outcome = __import__("game.tasks", fromlist=["validate_task"]).validate_task(task, task["solution"])
            assert outcome.passed, (rid, seed, task["title"], outcome.to_dict())


def test_generate_challenge_randomness():
    """同一种子重复生成应一致，不同种子应产生不同挑战。"""
    a = secret_realms.generate_challenge("qingyun", random.Random(1))
    b = secret_realms.generate_challenge("qingyun", random.Random(1))
    assert a["title"] == b["title"] and a["story"] == b["story"]
    seen = set()
    for seed in range(12):
        c = secret_realms.generate_challenge("qingyun", random.Random(seed))
        seen.add((c["title"], c["story"]))
    assert len(seen) >= 3, seen


def test_sanitize_hides_solution():
    task = secret_realms.generate_challenge("qingyun", random.Random(3))
    sani = secret_realms.sanitize(task)
    assert "solution" not in sani and "check" not in sani
    for key in ("id", "kind", "title", "story", "hints", "starter_code", "no_solution", "secret_realm", "time_limit"):
        assert key in sani


def test_generate_unknown_realm():
    with pytest.raises(ValueError):
        secret_realms.generate_challenge("nope")


# ---------- 门槛判定 ----------

def test_is_enterable_gate():
    p = Player(realm_key="qi1")
    realms = secret_realms.secret_realms()
    # 未解锁
    assert secret_realms.is_enterable(p, realms["qingyun"]) is False
    # 已解锁但境界不足
    _unlock_and_realm(p, "qingyun", "qi1")
    assert secret_realms.is_enterable(p, realms["qingyun"]) is False
    # 境界在区间内
    _unlock_and_realm(p, "qingyun", "qi5")
    assert secret_realms.is_enterable(p, realms["qingyun"]) is True
    # 超出上限
    _unlock_and_realm(p, "qingyun", "gold1")
    assert secret_realms.is_enterable(p, realms["qingyun"]) is False


def test_wanxiang_and_tiangong_gates():
    realms = secret_realms.secret_realms()
    p = Player(realm_key="gold1")
    _unlock_and_realm(p, "wanxiang", "gold1")
    assert secret_realms.is_enterable(p, realms["wanxiang"]) is True
    p.realm_key = "nas2"
    assert secret_realms.is_enterable(p, realms["wanxiang"]) is True
    p.realm_key = "spr1"
    assert secret_realms.is_enterable(p, realms["wanxiang"]) is False

    p2 = Player(realm_key="nas1")
    _unlock_and_realm(p2, "tiangong", "nas1")
    assert secret_realms.is_enterable(p2, realms["tiangong"]) is False
    p2.realm_key = "spr1"
    assert secret_realms.is_enterable(p2, realms["tiangong"]) is True


# ---------- 奖励 ----------

def test_apply_clear_first_and_repeat():
    p = Player(realm_key="qi5")
    p.secret_unlocked.append("qingyun")
    task = secret_realms.generate_challenge("qingyun", random.Random(5))
    before = p.cultivation
    r1 = secret_realms.apply_clear(p, "qingyun", task)
    assert r1["first_clear"] is True and r1["cleared_count"] == 1
    assert r1["rewards"]["cultivation"] == 150
    assert p.cultivation == before + 150
    assert p.secret_log == {"qingyun": 1}

    r2 = secret_realms.apply_clear(p, "qingyun", task)
    assert r2["first_clear"] is False and r2["cleared_count"] == 2
    assert r2["rewards"]["cultivation"] == 60
    assert p.cultivation == before + 150 + 60


def test_secret_achievements():
    p = Player()
    p.secret_log["qingyun"] = 1
    unlocked = achievements.check_all(p)
    ids = {a["id"] for a in unlocked}
    assert "secret_qingyun" in ids
    assert "secret_pilgrim" not in ids
    p.secret_log["wanxiang"] = 1
    p.secret_log["tiangong"] = 1
    ids2 = {a["id"] for a in achievements.check_all(p)}
    assert {"secret_wanxiang", "secret_tiangong", "secret_pilgrim"} <= ids2
    assert p.title == "秘境行者"


# ---------- API ----------

def test_secret_realms_requires_player(client):
    resp = client.get("/api/secret-realms")
    assert resp.status_code == 400


def test_secret_api_flow(client, new_player):
    # 初始：三秘境均未解锁
    resp = client.get("/api/secret-realms")
    realms = resp.get_json()["secret_realms"]
    assert {r["id"] for r in realms} == set(REALM_IDS)
    assert all(r["unlocked"] is False for r in realms)

    # 未解锁进入 -> 403
    resp = client.post("/api/secret-realms/qingyun/enter")
    assert resp.status_code == 403

    # 对话解锁青云秘境
    resp = client.get("/api/dialogues/guide_realm")
    node = resp.get_json()["dialogue"]
    resp = client.post("/api/dialogues/guide_realm/choose",
                       json={"node_id": node["node_id"], "option_index": 0})
    assert resp.status_code == 200
    realms = resp.get_json()["state"]["secret_realms"]
    assert next(r for r in realms if r["id"] == "qingyun")["unlocked"] is True

    # 境界不足 -> 403
    resp = client.post("/api/secret-realms/qingyun/enter")
    assert resp.status_code == 403

    # 提升境界后进入
    from game import server as server_mod
    server_mod._current_player.realm_key = "qi5"
    resp = client.post("/api/secret-realms/qingyun/enter")
    assert resp.status_code == 200
    challenge = resp.get_json()["challenge"]
    assert "solution" not in challenge and "check" not in challenge
    assert challenge["secret_realm"] == "qingyun"

    # 运行
    resp = client.post("/api/secret-realms/qingyun/run", json={"code": challenge["starter_code"]})
    assert resp.status_code == 200
    assert resp.get_json()["run"]["status"] == "ok"

    # 错误提交 -> 失败，心境下降
    before_mind = server_mod._current_player.mindset
    resp = client.post("/api/secret-realms/qingyun/submit", json={"code": "print(0)"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["outcome"]["passed"] is False
    assert data["state"]["player"]["mindset"] == before_mind - 2

    # 正确提交（用服务端持有的参考答案）
    sol = server_mod._secret_challenges["qingyun"]["solution"]
    resp = client.post("/api/secret-realms/qingyun/submit", json={"code": sol})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["outcome"]["passed"] is True
    assert data["events"]["first_clear"] is True
    assert data["events"]["cleared_count"] == 1
    assert data["events"]["rewards"]["cultivation"] == 150
    cleared = next(r for r in data["state"]["secret_realms"] if r["id"] == "qingyun")
    assert cleared["cleared"] == 1
    ach_ids = {a["id"] for a in data["new_achievements"]}
    assert "secret_qingyun" in ach_ids


def test_secret_submit_without_enter(client, new_player):
    resp = client.post("/api/secret-realms/qingyun/submit", json={"code": "print(1)"})
    assert resp.status_code == 400


def test_secret_run_without_enter(client, new_player):
    resp = client.post("/api/secret-realms/qingyun/run", json={"code": "print(1)"})
    assert resp.status_code == 400


def test_secret_unknown_realm(client, new_player):
    resp = client.post("/api/secret-realms/nope/enter")
    assert resp.status_code == 404


def test_secret_guidance_supports_challenge(client, new_player):
    """师尊接口应能对当前秘境挑战给出引导。"""
    from game import server as server_mod
    server_mod._current_player.secret_unlocked.append("qingyun")
    server_mod._current_player.realm_key = "qi5"
    resp = client.post("/api/secret-realms/qingyun/enter")
    assert resp.status_code == 200
    resp = client.post("/api/ai/guidance", json={"task_id": "secret:qingyun", "hint_level": 1})
    assert resp.status_code == 200
    assert resp.get_json()["text"]


def test_dialogue_unlocks_wanxiang_tiangong(client, new_player):
    """秘境引路人可分别解锁三个秘境。"""
    resp = client.get("/api/dialogues/guide_realm")
    node = resp.get_json()["dialogue"]
    # 万象幻境（第 2 个选项）
    resp = client.post("/api/dialogues/guide_realm/choose",
                       json={"node_id": "start", "option_index": 1})
    assert resp.status_code == 200
    state = resp.get_json()["state"]
    assert "wanxiang" in state["player"]["secret_unlocked"]
    # 代码天宫（第 3 个选项）
    resp = client.post("/api/dialogues/guide_realm/choose",
                       json={"node_id": "start", "option_index": 2})
    assert resp.status_code == 200
    state = resp.get_json()["state"]
    assert "tiangong" in state["player"]["secret_unlocked"]