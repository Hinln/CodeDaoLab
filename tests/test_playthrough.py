# -*- coding: utf-8 -*-
"""完整通关验收测试：凡人 → 学习 → 任务 → Debug → 筑基天劫 → 筑基成功。

对应 ACCEPTANCE_CRITERIA.md 的 V0.1 验收标准中的游戏流程闭环。
"""

import json

from game import curriculum


def _complete_main_line(client):
    """按顺序完成全部主线任务并突破到炼气大圆满。"""
    realm_keys = ["mortal", "qi1", "qi2", "qi3", "qi4", "qi5", "qi6", "qi7", "qi8", "qi9", "qi10"]
    for realm_key in realm_keys:
        for task_id in curriculum.realm_tasks(realm_key):
            task = curriculum.get_task(task_id)
            resp = client.post(f"/api/tasks/{task_id}/submit", json={"code": task["solution"]})
            data = resp.get_json()
            assert data["outcome"]["passed"] is True, (realm_key, task_id, data["outcome"])
        if realm_key == "qi10":
            # ??????????????????
            state = client.get("/api/state").get_json()
            assert state["pending_breakthrough"] is True
            assert state["tribulation"]["unlocked"] is True
            resp = client.post("/api/breakthrough")
            assert resp.status_code == 400
        else:
            resp = client.post("/api/breakthrough")
            assert resp.status_code == 200, (realm_key, resp.get_json())


def _complete_all_debug_tasks(client, state):
    """完成所有已解锁炼丹房任务。"""
    debug_list = curriculum.tasks()["debug_tasks"]
    while True:
        state = client.get("/api/state").get_json()
        unlocked = [d["id"] for d in state["debug_tasks"]]
        if not unlocked:
            break
        for task_id in unlocked:
            task = curriculum.get_task(task_id)
            resp = client.post(f"/api/tasks/{task_id}/submit", json={"code": task["solution"]})
            assert resp.get_json()["outcome"]["passed"] is True, task_id
    # 只要求完成「当前境界已解锁」的心魔任务（高境界 Debug 留待后续内容）
    player_order = curriculum.realm_order(state["player"]["realm_key"])
    expected_done = [
        d for d in debug_list
        if curriculum.realm_order(curriculum.debug_unlock_map().get(d, "")) <= player_order
    ]
    assert len(state["player"]["debug_completed"]) == len(expected_done)


def _complete_tribulation(client):
    """渡过三道天劫并筑基。"""
    waves = sorted(curriculum.tribulation_waves().values(), key=lambda w: w["order"])
    for wave in waves:
        task = curriculum.get_task(wave["task"])
        resp = client.post(f"/api/tasks/{task['id']}/submit", json={"code": task["solution"]})
        data = resp.get_json()
        assert data["outcome"]["passed"] is True, wave["key"]
        assert data["state"]["tribulation"]["waves"][wave["order"] - 1]["passed"] is True
    resp = client.post("/api/breakthrough")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["event"]["founded"] is True
    return data


def test_full_playthrough_to_foundation(client):
    """完整通关：建角色 → 全部主线 → Debug → 天劫 → 筑基。"""
    resp = client.post("/api/game/new", json={"name": "验收修士", "spirit_root": "火"})
    assert resp.status_code == 200
    assert resp.get_json()["player"]["realm_key"] == "mortal"

    _complete_main_line(client)
    state = client.get("/api/state").get_json()
    assert state["player"]["realm_key"] == "qi10"
    assert state["pending_breakthrough"] is True

    _complete_all_debug_tasks(client, state)
    data = _complete_tribulation(client)
    state = data["state"]
    assert state["player"]["founded"] is True
    assert state["player"]["realm_key"] == "foundation"
    assert state["realm"]["name"] == "筑基"

    # 存档可在新会话恢复
    import game.server as server_mod
    server_mod._current_player = None
    resp = client.post("/api/game/load")
    assert resp.status_code == 200
    loaded = resp.get_json()
    assert loaded["player"]["founded"] is True
    assert loaded["player"]["realm_key"] == "foundation"


def test_playthrough_cultivation_increases(client):
    """Cultivation keeps growing through the playthrough, and save stays complete.

    Since V0.2, cultivation sources include task rewards AND achievement
    rewards (e.g. first_awaken +10), so assert cultivation is strictly
    increasing and never below the summed task rewards.
    """
    client.post("/api/game/new", json={"name": "Xiaoshitou"})
    total_reward = 0
    prev_cultivation = 0
    for realm_key in ["mortal", "qi1", "qi2"]:
        for task_id in curriculum.realm_tasks(realm_key):
            task = curriculum.get_task(task_id)
            resp = client.post(f"/api/tasks/{task_id}/submit", json={"code": task["solution"]})
            total_reward += task.get("reward", 0)
            data = resp.get_json()
            cultivation = data["state"]["player"]["cultivation"]
            assert cultivation >= total_reward, (task_id, cultivation, total_reward)
            assert cultivation > prev_cultivation, (task_id, cultivation, prev_cultivation)
            prev_cultivation = cultivation
        client.post("/api/breakthrough")
    state = client.get("/api/state").get_json()
    assert state["player"]["cultivation"] >= total_reward
def test_wrong_code_does_not_advance(client):
    """错误的代码不会推进进度。"""
    client.post("/api/game/new", json={"name": "懒道人"})
    for _ in range(3):
        resp = client.post("/api/tasks/tutorial_run/submit", json={"code": "print('错误答案')"})
        assert resp.get_json()["outcome"]["passed"] is False
        assert resp.get_json()["state"]["player"]["completed_tasks"] == []
        assert resp.get_json()["state"]["player"]["pending_breakthrough"] is False
