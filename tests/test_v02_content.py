# -*- coding: utf-8 -*-
"""V0.2 阶段五 · Python 内容扩充验收测试。

覆盖：新境界链（金丹/元婴/化神）、字符串/异常/模块/文件/OOP 五大知识点、
综合试炼可见性、方法/异常验证模式、Debug 解锁、境界成就。
"""

import pytest

from game import achievements, curriculum, tasks
from game.player import Player

NEW_REALMS = ["gold1", "gold2", "nas1", "nas2", "spr1"]
MAIN_TASKS = ["str_essence", "exc_guard", "mod_import", "file_scripture", "oop_spirit"]
TRIAL_TASKS = ["str_trial", "exc_trial", "mod_trial", "file_trial", "oop_trial"]
DEBUG_TASKS = ["debug_str", "debug_exc", "debug_mod", "debug_file", "debug_oop"]

# 试炼无参考答案字段，这里给出用于验证的解法
TRIAL_SOLUTIONS = {
    "str_trial": "def transform(text):\n    return text.strip().upper().replace(\" \", \"_\")",
    "exc_trial": (
        "def take_essence(data, key):\n"
        "    if key not in data:\n"
        "        raise ValueError(\"缺少\" + key)\n"
        "    return data[key]"
    ),
    "mod_trial": (
        "with open(\"base.py\", \"w\", encoding=\"utf-8\") as f:\n"
        "    f.write(\"def power(x):\\n    return x * x\\n\")\n"
        "with open(\"art.py\", \"w\", encoding=\"utf-8\") as f:\n"
        "    f.write(\"def double(x):\\n    return x * 2\\n\")\n\n"
        "from base import power\n"
        "from art import double\n"
        "print(power(double(5)))"
    ),
    "file_trial": (
        "with open(\"丹方.txt\", \"w\", encoding=\"utf-8\") as f:\n"
        "    f.writelines([\"聚气丹：1\\n\", \"凝神丹：2\\n\", \"培元丹：3\\n\"])\n\n"
        "with open(\"丹方.txt\", encoding=\"utf-8\") as f:\n"
        "    total = 0\n"
        "    for line in f:\n"
        "        total += int(line.strip().split(\"：\")[1])\n\n"
        "print(total)"
    ),
    "oop_trial": (
        "class Spirit:\n"
        "    def __init__(self, name, level):\n"
        "        self.name = name\n"
        "        self.level = level\n\n"
        "    def train(self):\n"
        "        self.level += 1\n"
        "        return self.level\n\n"
        "    def report(self):\n"
        "        return f\"{self.name} 境界：{self.level}\"\n\n"
        "s = Spirit(\"剑灵\", 1)\n"
        "print(s.train())\n"
        "print(s.report())"
    ),
}


def _solution(task_id):
    task = curriculum.get_task(task_id)
    if task.get("kind") == "trial":
        return TRIAL_SOLUTIONS[task_id]
    return task["solution"]


# ---------- 课程数据 ----------

def test_new_realms_in_chain():
    orders = [curriculum.realm_order(k) for k in NEW_REALMS]
    assert orders == sorted(orders)
    assert curriculum.next_realm_key("foundation") == "gold1"
    assert curriculum.next_realm_key("gold1") == "gold2"
    assert curriculum.next_realm_key("nas1") == "nas2"
    assert curriculum.next_realm_key("spr1") is None


def test_major_realm_stages():
    major = {m["key"]: m for m in curriculum.major_realms()}
    assert major["golden_core"]["stages"] == ["gold1", "gold2"]
    assert major["nascent_soul"]["stages"] == ["nas1", "nas2"]
    assert major["spirit_transformation"]["stages"] == ["spr1"]
    assert curriculum.major_realm_for("gold1")["name"] == "金丹"
    assert curriculum.major_realm_for("nas2")["name"] == "元婴"
    assert curriculum.major_realm_for("spr1")["name"] == "化神"


def test_new_debug_unlock():
    unlock = curriculum.debug_unlock_map()
    for dbg, realm in zip(DEBUG_TASKS, NEW_REALMS):
        assert unlock[dbg] == realm


def test_foundation_task_added():
    assert "foundation_consolidation" in curriculum.realm_tasks("foundation")
    assert curriculum.get_task("foundation_consolidation")["kind"] == "main"


# ---------- 任务验证（真实执行） ----------

@pytest.mark.parametrize("task_id", MAIN_TASKS + TRIAL_TASKS + DEBUG_TASKS + ["foundation_consolidation"])
def test_solution_passes(task_id):
    task = curriculum.get_task(task_id)
    assert task is not None
    outcome = tasks.validate_task(task, _solution(task_id))
    assert outcome.passed, (task_id, outcome.to_dict())


def test_trials_have_no_solution_and_7_elements():
    for tid in TRIAL_TASKS:
        task = curriculum.get_task(tid)
        assert task["no_solution"] is True
        assert "solution" not in task
        assert task["kind"] == "trial"
        assert task["hints"], tid
        # 综合试炼所属境界的教学包含剧情/功法介绍/教学/示例
        realm = curriculum.realm_by_key(task["realm"])
        titles = [t["title"] for t in realm["teaching"]]
        assert any("剧情" in t for t in titles), (tid, titles)
        assert any("功法介绍" in t for t in titles), (tid, titles)
        assert any("教学" in t for t in titles), (tid, titles)
        assert any("示例" in t for t in titles), (tid, titles)


def test_each_knowledge_realm_has_main_debug_trial():
    pairs = {
        "gold1": ("str_essence", "debug_str", "str_trial"),
        "gold2": ("exc_guard", "debug_exc", "exc_trial"),
        "nas1": ("mod_import", "debug_mod", "mod_trial"),
        "nas2": ("file_scripture", "debug_file", "file_trial"),
        "spr1": ("oop_spirit", "debug_oop", "oop_trial"),
    }
    for realm_key, (main_id, debug_id, trial_id) in pairs.items():
        assert main_id in curriculum.realm_tasks(realm_key)
        assert trial_id in curriculum.realm_tasks(realm_key)
        assert curriculum.get_task(debug_id)["realm"] == realm_key


def test_method_validation_mode():
    """OOP 任务使用方法验证模式（class + init_args + method）。"""
    task = curriculum.get_task("oop_spirit")
    outcome = tasks.validate_task(task, task["solution"])
    assert outcome.passed
    assert all(d["pass"] for d in outcome.details)


def test_raises_validation_mode():
    """异常试炼支持 expects-raises 用例。"""
    task = curriculum.get_task("exc_trial")
    outcome = tasks.validate_task(task, TRIAL_SOLUTIONS["exc_trial"])
    assert outcome.passed
    assert all(d["pass"] for d in outcome.details)


# ---------- 试炼可见性 ----------

def test_trial_visible_only_as_current_task():
    p = Player(realm_key="gold1")
    trial = curriculum.get_task("str_trial")
    main = curriculum.get_task("str_essence")
    assert tasks.task_visible_kind(p, trial) is None  # 主线未完成，试炼不可见
    p.completed_tasks.append("str_essence")
    assert tasks.task_visible_kind(p, trial) == tasks.TRIAL
    other = Player(realm_key="gold2")
    assert tasks.task_visible_kind(other, trial) is None  # 其他境界不可见


def test_debug_tasks_unlock_by_realm():
    p = Player(realm_key="gold1")
    unlocked = tasks.unlocked_debug_tasks(p)
    assert "debug_str" in unlocked
    assert "debug_exc" not in unlocked
    p2 = Player(realm_key="nas1")
    u2 = tasks.unlocked_debug_tasks(p2)
    assert "debug_str" in u2 and "debug_mod" in u2
    assert "debug_oop" not in u2


# ---------- 境界成就 ----------

def test_realm_achievements_unlock_on_breakthrough():
    p = Player(realm_key="foundation", completed_tasks=list(curriculum.realm_tasks("foundation")))
    p.pending_breakthrough = True
    # 模拟突破到 gold1
    p.realm_key = "gold1"
    new = achievements.check_all(p)
    ids = [a["id"] for a in new]
    assert "realm_golden" in ids
    assert p.title == "金丹修士"


# ---------- 完整链条通关 ----------

def test_playthrough_foundation_to_spirit(client):
    """从建角一路打通到化神一层（含筑基道基巩固）。"""
    resp = client.post("/api/game/new", json={"name": "通天道人", "spirit_root": "木"})
    assert resp.status_code == 200

    def submit(tid):
        resp = client.post(f"/api/tasks/{tid}/submit", json={"code": _solution(tid)})
        data = resp.get_json()
        assert data["outcome"]["passed"] is True, (tid, data["outcome"])
        return data

    def clear_debugs():
        while True:
            state = client.get("/api/state").get_json()
            if not state["debug_tasks"]:
                return
            for d in state["debug_tasks"]:
                submit(d["id"])

    for realm_key in ["mortal", "qi1", "qi2", "qi3", "qi4", "qi5", "qi6", "qi7", "qi8", "qi9", "qi10"]:
        for tid in curriculum.realm_tasks(realm_key):
            submit(tid)
        if realm_key != "qi10":
            assert client.post("/api/breakthrough").status_code == 200, realm_key
    clear_debugs()
    state = client.get("/api/state").get_json()
    for w in state["tribulation"]["waves"]:
        submit(w["task_id"])
    assert client.post("/api/breakthrough").get_json()["event"]["founded"] is True

    chain = ["foundation", "gold1", "gold2", "nas1", "nas2", "spr1"]
    for idx, realm_key in enumerate(chain):
        state = client.get("/api/state").get_json()
        assert state["player"]["realm_key"] == realm_key
        for tid in curriculum.realm_tasks(realm_key):
            submit(tid)
        clear_debugs()
        state = client.get("/api/state").get_json()
        assert state["pending_breakthrough"] is True, realm_key
        if idx == len(chain) - 1:
            resp = client.post("/api/breakthrough")
            assert resp.status_code == 400
            assert "已至尽头" in resp.get_json()["error"]
        else:
            assert client.post("/api/breakthrough").status_code == 200, realm_key

    state = client.get("/api/state").get_json()
    assert state["player"]["realm_key"] == "spr1"
    assert state["realm"]["major"]["name"] == "化神"
    unlocked = [a["id"] for a in state["achievements"] if a["unlocked"]]
    assert {"realm_golden", "realm_nascent", "realm_spirit"} <= set(unlocked)
    assert state["player"]["title"] == "化神真君"