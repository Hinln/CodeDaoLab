# -*- coding: utf-8 -*-
"""任务数据与验证引擎测试：确保所有任务可用参考答案通关。"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from game import curriculum, tasks
from game.player import Player

ALL_TASKS = curriculum.all_tasks()


@pytest.mark.parametrize("task_id", sorted(ALL_TASKS))
def test_solution_passes(task_id):
    task = ALL_TASKS[task_id]
    if task.get("no_solution"):
        pytest.skip("试炼任务无参考答案，解法在 test_v02_content 中验证")
    assert task.get("solution"), task_id
    outcome = tasks.validate_task(task, task["solution"])
    assert outcome.passed, (task_id, outcome.run.status, outcome.run.message, outcome.details)


@pytest.mark.parametrize("task_id", sorted(ALL_TASKS))
def test_empty_code_fails(task_id):
    task = ALL_TASKS[task_id]
    outcome = tasks.validate_task(task, "pass")
    assert not outcome.passed, task_id


@pytest.mark.parametrize("task_id", sorted(ALL_TASKS))
def test_buggy_starter_fails(task_id):
    """debug 任务的初始心魔代码必须无法通过验证（否则没有修复的意义）。"""
    task = ALL_TASKS[task_id]
    if task.get("kind") != "debug":
        pytest.skip("仅 debug 任务")
    outcome = tasks.validate_task(task, task["starter_code"])
    assert not outcome.passed, task_id


def test_function_task_rejects_wrong_name():
    task = ALL_TASKS["functions"]
    outcome = tasks.validate_task(task, "def double2(x):\n    return x * 2")
    assert not outcome.passed
    assert any("未找到函数" in str(d.get("reason", "")) for d in outcome.details)


def test_function_task_rejects_wrong_logic():
    task = ALL_TASKS["conditionals"]
    outcome = tasks.validate_task(task, "def judge(power):\n    return \"筑基\"")
    assert not outcome.passed
    assert any(not d["pass"] for d in outcome.details)


def test_output_task_rejects_wrong_output():
    task = ALL_TASKS["hello_world"]
    outcome = tasks.validate_task(task, "print(\"Hello World!\")")
    assert not outcome.passed
    assert outcome.details and outcome.details[0]["pass"] is False


def test_output_task_accepts_with_inputs():
    task = ALL_TASKS["input_output"]
    outcome = tasks.validate_task(task, "name = input()\nprint(\"道友\" + name + \"，欢迎入道！\")")
    assert outcome.passed


def test_debug_unlock_order():
    p = Player(realm_key="qi3")
    unlocked = tasks.unlocked_debug_tasks(p)
    assert "debug_1" in unlocked
    assert "debug_2" not in unlocked
    p2 = Player(realm_key="qi6")
    u2 = tasks.unlocked_debug_tasks(p2)
    assert "debug_1" in u2 and "debug_2" in u2
    assert "debug_3" not in u2


def test_tribulation_unlock_only_at_qi10():
    p = Player(realm_key="qi9")
    assert not tasks.is_tribulation_unlocked(p)
    p2 = Player(realm_key="qi10", completed_tasks=curriculum.realm_tasks("qi10"))
    assert tasks.is_tribulation_unlocked(p2)


def test_current_task_progression():
    p = Player()
    assert tasks.current_task_id(p) == "tutorial_run"
    p.completed_tasks.append("tutorial_run")
    assert tasks.current_task_id(p) is None
    assert p.pending_breakthrough is False  # 尚未调用突破

    ev = tasks.complete_main_task(p, curriculum.get_task("tutorial_run"))
    assert ev["realm_complete"] is True
    assert p.pending_breakthrough is True
    assert p.cultivation == 50

    b = tasks.breakthrough(p)
    assert b["type"] == "breakthrough"
    assert p.realm_key == "qi1"
    assert tasks.current_task_id(p) == "hello_world"


def test_full_main_line_playthrough():
    """从凡人到筑基大圆满的完整主线推进（不渡劫）。"""
    p = Player()
    realm_keys = ["mortal", "qi1", "qi2", "qi3", "qi4", "qi5", "qi6", "qi7", "qi8", "qi9", "qi10"]
    for realm_key in realm_keys:
        for task_id in curriculum.realm_tasks(realm_key):
            task = curriculum.get_task(task_id)
            outcome = tasks.validate_task(task, task["solution"])
            assert outcome.passed, (realm_key, task_id)
            tasks.complete_main_task(p, task)
        assert p.pending_breakthrough is True, realm_key
        if realm_key != "qi10":
            tasks.breakthrough(p)
        else:
            # 大圆满：渡劫台开启，但未渡劫前无法突破
            assert tasks.is_tribulation_unlocked(p)
            with pytest.raises(ValueError):
                tasks.breakthrough(p)
    assert p.realm_key == "qi10"
    assert p.founded is False


def test_tribulation_flow():
    """渡劫三关 + 筑基。"""
    p = Player(realm_key="qi10", completed_tasks=list(curriculum.realm_tasks("qi10")))
    p.pending_breakthrough = True
    waves = sorted(curriculum.tribulation_waves().values(), key=lambda w: w["order"])
    for wave in waves:
        task = curriculum.get_task(wave["task"])
        assert tasks.current_wave_key(p) == wave["key"]
        outcome = tasks.validate_task(task, task["solution"])
        assert outcome.passed, wave["key"]
        tasks.complete_wave(p, task)
    assert tasks.current_wave_key(p) is None
    b = tasks.breakthrough(p)
    assert b["founded"] is True
    assert p.founded is True
    assert p.realm_key == "foundation"
