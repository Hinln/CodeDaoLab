# -*- coding: utf-8 -*-
"""pytest 公共夹具：隔离存档目录、重置游戏会话。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import config, server, save


@pytest.fixture()
def app(tmp_path):
    """隔离存档目录并返回 Flask 测试应用。"""
    old_save_dir = config.SAVE_DIR
    config.SAVE_DIR = str(tmp_path / "saves")
    server._current_player = None
    server._secret_challenges = {}
    app = server.create_app()
    app.config.update(TESTING=True)
    yield app
    config.SAVE_DIR = old_save_dir
    server._current_player = None
    server._secret_challenges = {}


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def new_player(client):
    """创建一位新角色并返回其初始状态。"""
    resp = client.post("/api/game/new", json={"name": "测试修士", "spirit_root": "金"})
    assert resp.status_code == 200
    return resp.get_json()


def submit_solution(client, task_id, solution):
    """提交参考答案并断言通过，返回响应 JSON。"""
    resp = client.post(f"/api/tasks/{task_id}/submit", json={"code": solution})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["outcome"]["passed"] is True, (task_id, data["outcome"])
    return data
