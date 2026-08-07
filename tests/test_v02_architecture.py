# -*- coding: utf-8 -*-
"""V0.2 架构升级测试：多存档、NPC、对话、功法、道具、支线任务。"""

from game import curriculum, dialogues, items, npcs, save, techniques
from game.player import Player


# ---------- 多存档 ----------

def test_multi_slot_save_load_delete(client):
    r1 = client.post("/api/game/new", json={"name": "甲修士", "slot": "slot_a"})
    assert r1.status_code == 200
    r2 = client.post("/api/game/new", json={"name": "乙修士", "slot": "slot_b"})
    assert r2.status_code == 200

    slots = client.get("/api/slots").get_json()["slots"]
    names = {s["slot"]: s["player"]["name"] for s in slots}
    assert names == {"slot_a": "甲修士", "slot_b": "乙修士"}

    resp = client.post("/api/game/load", json={"slot": "slot_a"})
    assert resp.get_json()["player"]["name"] == "甲修士"

    resp = client.post("/api/game/delete", json={"slot": "slot_b"})
    assert resp.get_json()["ok"] is True
    assert client.post("/api/game/delete", json={"slot": "slot_b"}).status_code == 404


def test_state_without_game_lists_slots(app, client, tmp_path):
    from game import config as cfg
    old = cfg.SAVE_DIR
    cfg.SAVE_DIR = str(tmp_path / "s2")
    import game.server as server_mod
    server_mod._current_player = None
    try:
        resp = client.get("/api/state")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["player"] is None
        assert data["slots"] == []
    finally:
        cfg.SAVE_DIR = old
        server_mod._current_player = None


# ---------- NPC ----------

def test_npc_list(client, new_player):
    data = client.get("/api/npcs").get_json()
    ids = {n["id"] for n in data["npcs"]}
    assert {"master_qingxuan", "elder_library", "steward_pill", "guide_realm", "disciple_xiaoyue"} <= ids


def test_npcs_data_consistency():
    """每个 NPC 的对话树必须存在，且所有 goto 指向有效节点。"""
    for npc in npcs.all_npcs():
        tree = dialogues.get_tree(npc["id"])
        assert tree, npc["id"]
        for node_id, node in tree.items():
            for opt in node.get("options", []):
                target = opt.get("goto")
                assert target in tree or target == "__end__", (npc["id"], node_id, target)


# ---------- 对话 ----------

def test_dialogue_enter_and_choose(client, new_player):
    resp = client.get("/api/dialogues/elder_library")
    assert resp.status_code == 200
    dlg = resp.get_json()["dialogue"]
    assert dlg["node_id"] == "start"
    assert dlg["options"]

    resp = client.post("/api/dialogues/elder_library/choose",
                       json={"node_id": "start", "option_index": 0})
    data = resp.get_json()
    assert data["dialogue"]["node_id"] == "herb_quest"
    assert "branch_herbs" in data["state"]["player"]["branch_unlocked"]


def test_dialogue_reward_once(client, new_player):
    for _ in range(2):
        resp = client.post("/api/dialogues/master_qingxuan/choose",
                           json={"node_id": "start", "option_index": 1})
        assert resp.status_code == 200
    state = client.get("/api/state").get_json()
    assert state["player"]["comprehension"] == 11  # 默认 10 + 1，只加一次
    assert state["player"]["mindset"] == 110


def test_dialogue_unknown_npc(client, new_player):
    resp = client.get("/api/dialogues/nobody")
    assert resp.status_code == 404


def test_dialogue_invalid_option(client, new_player):
    resp = client.post("/api/dialogues/elder_library/choose",
                       json={"node_id": "start", "option_index": 99})
    assert resp.status_code == 400


# ---------- 功法 ----------

def test_techniques_in_state_and_api(client, new_player):
    state = client.get("/api/state").get_json()
    techs = state["techniques"]
    assert len(techs) == len(techniques.all_techniques())
    unlocked = {t["id"] for t in techs if t["unlocked"]}
    assert unlocked == {"mortal"}  # 新建角色仅习得凡人功法

    data = client.get("/api/techniques").get_json()
    assert len(data["techniques"]) == len(techniques.all_techniques())


def test_breakthrough_learns_technique(client, new_player):
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"})
    resp = client.post("/api/breakthrough")
    state = resp.get_json()["state"]
    assert state["player"]["realm_key"] == "qi1"
    assert "qi1" in state["player"]["techniques"]


def test_technique_accessor():
    assert techniques.get_technique("qi3")["name"] == "炼气三层"
    assert techniques.get_technique("nope") is None


# ---------- 道具 ----------

def test_item_use(client, new_player):
    # 通过支线奖励获得道具（branch_herbs 无道具，直接手动加）
    import game.server as server_mod
    player = server_mod._current_player
    player.add_item("jingxin_dan", 2)
    server_mod.save.save_game(player)

    resp = client.post("/api/items/jingxin_dan/use")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["result"]["used"] is True
    assert data["state"]["player"]["mindset"] == 130
    assert data["state"]["player"]["items"]["jingxin_dan"] == 1

    # 未拥有道具
    resp = client.post("/api/items/wudao_dan/use")
    assert resp.status_code == 400


def test_items_defs():
    assert items.get_item("wudao_dan")["effect"] == {"comprehension": 1}


# ---------- 支线任务 ----------

def test_branch_task_requires_realm(client, new_player):
    """支线解锁后，境界不足时不可见。"""
    # 通过对话解锁 branch_herbs（requires_realm=qi7）
    client.post("/api/dialogues/elder_library/choose", json={"node_id": "start", "option_index": 0})
    resp = client.get("/api/tasks/branch_herbs")
    assert resp.status_code == 404
    state = client.get("/api/state").get_json()
    assert state["branch_tasks"] == []


def test_branch_task_full_flow(client):
    """推至 qi7 后完成采药支线。"""
    from tests.conftest import submit_solution
    client.post("/api/game/new", json={"name": "采药人", "spirit_root": "木"})
    from game import curriculum as cur
    for realm_key in ["mortal", "qi1", "qi2", "qi3", "qi4", "qi5", "qi6"]:
        for task_id in cur.realm_tasks(realm_key):
            task = cur.get_task(task_id)
            submit_solution(client, task_id, task["solution"])
        client.post("/api/breakthrough")

    client.post("/api/dialogues/elder_library/choose", json={"node_id": "start", "option_index": 0})
    state = client.get("/api/state").get_json()
    assert any(b["id"] == "branch_herbs" for b in state["branch_tasks"])

    # 错误代码不通过
    resp = client.post("/api/tasks/branch_herbs/submit", json={"code": "print('错')"})
    assert resp.get_json()["outcome"]["passed"] is False

    task = cur.get_task("branch_herbs")
    resp = client.post("/api/tasks/branch_herbs/submit", json={"code": task["solution"]})
    data = resp.get_json()
    assert data["outcome"]["passed"] is True
    assert "branch_herbs" in data["state"]["player"]["branch_completed"]
    assert data["state"]["player"]["comprehension"] >= 11

    # 完成后不再出现在支线列表
    state = client.get("/api/state").get_json()
    assert all(b["id"] != "branch_herbs" for b in state["branch_tasks"])


def test_all_tasks_have_valid_checks():
    """所有任务（含支线）必须有 solution 且验证结构合法。"""
    from game import tasks as tasks_mod
    for task_id, task in curriculum.all_tasks().items():
        assert task.get("solution") or task.get("no_solution"), task_id
        check = task.get("check", {})
        assert check.get("mode") in ("output", "function"), task_id
        if check["mode"] == "function":
            assert check.get("func_name") and check.get("cases"), task_id
        else:
            assert "expected" in check, task_id
        assert "story" in task and "hints" in task and "reward" in task
