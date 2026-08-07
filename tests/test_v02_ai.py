# -*- coding: utf-8 -*-
"""V0.2 AI 师尊系统测试。"""

import os

import pytest

from game import ai
from game.ai.local_tutor import LocalTutor
from game.ai.openai_tutor import OpenAICompatibleTutor
from game.player import Player


@pytest.fixture()
def tutor():
    return LocalTutor()


@pytest.fixture()
def player():
    return Player(name="测试修士")


def _ctx(task="tutorial_run", title="唤醒灵牌", attempts=0, level=None):
    ctx = {
        "task_id": task,
        "title": title,
        "hints": ["提示甲", "提示乙", "提示丙"],
        "attempts": attempts,
        "realm_key": "mortal",
    }
    if level is not None:
        ctx["hint_level"] = level
    return ctx


# ---------- 提示分级 ----------

def test_guidance_level1(tutor, player):
    text = tutor.guidance(player, _ctx(attempts=0))
    assert "方向" in text
    assert "参考答案" not in text


def test_guidance_level3_uses_hints(tutor, player):
    text = tutor.guidance(player, _ctx(attempts=3))
    assert "破局之钥" in text
    assert "提示乙" in text and "提示丙" in text


def test_guidance_level4_points_to_answer(tutor, player):
    text = tutor.guidance(player, _ctx(attempts=5, level=4))
    assert "参考答案" in text


def test_high_comprehension_advances_level(tutor):
    fast = Player(name="高悟性", comprehension=25)
    slow = Player(name="低悟性", comprehension=5)
    assert tutor.level_for(fast, 2) >= tutor.level_for(slow, 2)


def test_low_mindset_gets_more_hints(tutor):
    low = Player(name="心境低", mindset=20)
    high = Player(name="心境高", mindset=100)
    assert tutor.level_for(low, 1) >= tutor.level_for(high, 1)


# ---------- 错误分析 ----------

def test_analyze_syntax(tutor, player):
    text = tutor.error_analysis(player, {"status": "syntax", "error_line": 3})
    assert "语法" in text and "第 3 行" in text


def test_analyze_runtime(tutor, player):
    text = tutor.error_analysis(player, {"status": "runtime", "error_class": "NameError"})
    assert "NameError" in text


def test_analyze_timeout(tutor, player):
    assert "无限循环" in tutor.error_analysis(player, {"status": "timeout"})


def test_analyze_memory(tutor, player):
    assert "内存" in tutor.error_analysis(player, {"status": "memory"})


def test_analyze_output_mismatch(tutor, player):
    assert "输出" in tutor.error_analysis(player, {"status": "ok"})


def test_style_changes_by_realm(tutor):
    low = Player(name="凡人", realm_key="mortal")
    high = Player(name="高手", realm_key="qi10")
    assert tutor.error_analysis(low, {"status": "timeout"}) != tutor.error_analysis(high, {"status": "timeout"})


# ---------- 外部模型接口 ----------

def test_openai_provider_disabled_without_key():
    ot = OpenAICompatibleTutor()
    assert ot.enabled() is False


def test_create_tutor_defaults_to_local(monkeypatch):
    monkeypatch.delenv("CA_AI_BASE_URL", raising=False)
    monkeypatch.delenv("CA_AI_API_KEY", raising=False)
    assert isinstance(ai.create_tutor(), LocalTutor)


def test_openai_provider_falls_back_to_local(monkeypatch):
    ot = OpenAICompatibleTutor()
    ot.base_url = "http://127.0.0.1:1"   # 不可达
    ot.api_key = "sk-test"
    player = Player(name="x")
    text = ot.guidance(player, _ctx(attempts=0))
    assert "方向" in text  # 回退本地


# ---------- API ----------

def test_api_guidance(client, new_player):
    resp = client.post("/api/ai/guidance", json={"task_id": "tutorial_run"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["provider"] == "local"
    assert data["level"] == 1
    assert "方向" in data["text"]


def test_api_guidance_unknown_task(client, new_player):
    resp = client.post("/api/ai/guidance", json={"task_id": "hello_world"})
    assert resp.status_code == 404


def test_api_analyze(client, new_player):
    resp = client.post("/api/ai/analyze", json={"task_id": "tutorial_run", "code": "print('wrong')"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["run"]["status"] == "ok"
    assert "输出" in data["analysis"]


def test_failed_submit_increments_attempts(client, new_player):
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print('x')"})
    assert client.get("/api/state").get_json()["player"]["attempts"]["tutorial_run"] == 1
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print('x')"})
    assert client.get("/api/state").get_json()["player"]["attempts"]["tutorial_run"] == 2
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print('天地玄黄，宇宙洪荒。')"})
    state = client.get("/api/state").get_json()
    assert "tutorial_run" not in state["player"]["attempts"]


def test_guidance_level_after_failures(client, new_player):
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print('x')"})
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print('x')"})
    resp = client.post("/api/ai/guidance", json={"task_id": "tutorial_run"})
    assert resp.get_json()["level"] == 2
