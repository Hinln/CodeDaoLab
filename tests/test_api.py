# -*- coding: utf-8 -*-
"""后端 API 测试。"""

import pytest

from game import curriculum, tasks


def test_state_without_game(client):
    resp = client.get("/api/state")
    assert resp.status_code == 200
    assert resp.get_json()["player"] is None


def test_new_game(client, new_player):
    assert new_player["player"]["name"] == "测试修士"
    assert new_player["player"]["realm_key"] == "mortal"
    assert new_player["current_task"]["id"] == "tutorial_run"
    assert new_player["has_save"] is True


def test_run_endpoint(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/run", json={"code": "print('天地玄黄，宇宙洪荒。')"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["run"]["status"] == "ok"
    assert "天地玄黄" in data["run"]["stdout"]


def test_run_invalid_task(client, new_player):
    resp = client.post("/api/tasks/hello_world/run", json={"code": "print(1)"})
    assert resp.status_code == 404


def test_submit_wrong_then_right(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/submit", json={"code": "print('错误')"})
    assert resp.get_json()["outcome"]["passed"] is False
    assert "tutorial_run" not in resp.get_json()["state"]["player"]["completed_tasks"]

    resp = client.post(
        "/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"}
    )
    data = resp.get_json()
    assert data["outcome"]["passed"] is True
    assert data["state"]["player"]["pending_breakthrough"] is True


def test_breakthrough(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"})
    assert resp.get_json()["outcome"]["passed"] is True
    resp = client.post("/api/breakthrough")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["event"]["type"] == "breakthrough"
    assert data["state"]["player"]["realm_key"] == "qi1"
    assert data["state"]["current_task"]["id"] == "hello_world"


def test_breakthrough_rejected_when_not_ready(client, new_player):
    resp = client.post("/api/breakthrough")
    assert resp.status_code == 400


def test_save_and_load(client, new_player):
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"})
    client.post("/api/breakthrough")
    save_resp = client.post("/api/game/save")
    assert save_resp.get_json()["ok"] is True

    # 模拟重启：清空内存会话后从存档读取
    import game.server as server_mod
    server_mod._current_player = None
    resp = client.post("/api/game/load")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["player"]["realm_key"] == "qi1"


def test_debug_task_flow(client, new_player):
    # 推进到 qi3（解锁 debug_1）
    for realm_key in ("mortal", "qi1", "qi2"):
        for task_id in curriculum.realm_tasks(realm_key):
            task = curriculum.get_task(task_id)
            client.post(f"/api/tasks/{task_id}/submit", json={"code": task["solution"]})
        client.post("/api/breakthrough")

    state = client.get("/api/state").get_json()
    assert any(d["id"] == "debug_1" for d in state["debug_tasks"])

    # debug_1 用心魔代码提交应失败
    task = curriculum.get_task("debug_1")
    resp = client.post("/api/tasks/debug_1/submit", json={"code": task["starter_code"]})
    assert resp.get_json()["outcome"]["passed"] is False
    # 修复后通过
    resp = client.post("/api/tasks/debug_1/submit", json={"code": task["solution"]})
    assert resp.get_json()["outcome"]["passed"] is True
    assert "debug_1" in resp.get_json()["state"]["player"]["debug_completed"]


def test_tribulation_requires_full_qi(client, new_player):
    resp = client.post("/api/tasks/wave_heart_demon/submit", json={"code": "pass"})
    assert resp.status_code == 404
