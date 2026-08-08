# -*- coding: utf-8 -*-
"""V0.2 游戏化增强测试：成就、心境/连胜、大境界、称号。"""

from game import achievements, curriculum
from game.player import Player


# ---------- 成就条件 ----------

def test_achievement_task_done():
    pl = Player(name="甲")
    pl.completed_tasks.append("tutorial_run")
    new = achievements.check_all(pl)
    ids = {a["id"] for a in new}
    assert "first_awaken" in ids
    assert pl.cultivation == 10  # 奖励修为


def test_achievement_realm_reached():
    pl = Player(name="乙", realm_key="qi1")
    new = achievements.check_all(pl)
    ids = {a["id"] for a in new}
    assert "qi1_hello" in ids
    assert pl.title == "真言初成"
    assert pl.comprehension == 11


def test_achievement_streak():
    pl = Player(name="丙")
    pl.streak = 5
    new = achievements.check_all(pl)
    ids = {a["id"] for a in new}
    assert "streak_3" in ids and "streak_5" in ids
    assert pl.title == "行云流水"


def test_achievement_items_and_event():
    pl = Player(name="丁")
    pl.add_item("jingxin_dan", 1)
    new = achievements.check_all(pl)
    assert "items_first" in {a["id"] for a in new}
    new2 = achievements.check_all(pl, {"item_used": True})
    assert "item_use" in {a["id"] for a in new2}


def test_achievement_debug_and_foundation():
    pl = Player(name="戊")
    pl.debug_completed = ["debug_1", "debug_2", "debug_3", "debug_4"]
    pl.tribulation_passed = ["wave_1", "wave_2", "wave_3"]
    pl.founded = True
    new = achievements.check_all(pl)
    ids = {a["id"] for a in new}
    assert {"first_debug", "debug_four", "waves_all", "foundation"} <= ids
    assert pl.title == "筑基真人"


def test_achievement_no_duplicate():
    pl = Player(name="己")
    pl.completed_tasks.append("tutorial_run")
    achievements.check_all(pl)
    assert achievements.check_all(pl) == []


def test_achievement_cultivation():
    pl = Player(name="庚", cultivation=1200)
    new = achievements.check_all(pl)
    assert "cult_1000" in {a["id"] for a in new}
    assert pl.title == "灵力千钧"


def test_all_achievements_have_valid_data():
    for ach_id, ach in achievements.achievements().items():
        cond = ach.get("condition", {})
        assert cond.get("type"), ach_id
        assert ach.get("name") and ach.get("desc"), ach_id


# ---------- 心境 / 连胜（API） ----------

def test_failed_submit_penalizes_mindset(client, new_player):
    before = new_player["player"]["mindset"]
    resp = client.post("/api/tasks/tutorial_run/submit", json={"code": "print('错')"})
    data = resp.get_json()
    assert data["state"]["player"]["mindset"] == before - 2
    assert data["state"]["player"]["streak"] == 0


def test_success_increases_streak(client, new_player):
    resp = client.post("/api/tasks/tutorial_run/submit", json={"code": "print('天地玄黄，宇宙洪荒。')"})
    data = resp.get_json()
    assert data["state"]["player"]["streak"] == 1
    assert data["state"]["player"]["mindset"] == 102
    assert any(a["id"] == "first_awaken" for a in data["new_achievements"])


# ---------- 大境界 ----------

def test_major_realm_mapping():
    assert curriculum.major_realm_for("mortal")["name"] == "凡人"
    assert curriculum.major_realm_for("qi7")["name"] == "炼气"
    assert curriculum.major_realm_for("foundation")["name"] == "筑基"
    assert len(curriculum.major_realms()) == 10
    assert curriculum.major_realm_order("foundation") == 2


def test_state_contains_major_and_achievements(client, new_player):
    state = client.get("/api/state").get_json()
    assert state["realm"]["major"]["name"] == "凡人"
    assert len(state["achievements"]) == len(achievements.achievements())


def test_api_achievements(client, new_player):
    data = client.get("/api/achievements").get_json()
    assert len(data["achievements"]) == len(achievements.achievements())
    assert data["achievements"][0]["unlocked"] is False


def test_full_playthrough_unlocks_key_achievements(client):
    """完整通关后应解锁筑基相关成就。"""
    from tests.conftest import submit_solution
    client.post("/api/game/new", json={"name": "证道人"})
    for realm_key in ["mortal", "qi1", "qi2", "qi3", "qi4", "qi5", "qi6", "qi7", "qi8", "qi9", "qi10"]:
        for task_id in curriculum.realm_tasks(realm_key):
            task = curriculum.get_task(task_id)
            submit_solution(client, task_id, task["solution"])
        if realm_key != "qi10":
            client.post("/api/breakthrough")
    state = client.get("/api/state").get_json()
    assert state["player"]["pending_breakthrough"] is True
    # 炼丹房
    while True:
        state = client.get("/api/state").get_json()
        unlocked = [d["id"] for d in state["debug_tasks"]]
        if not unlocked:
            break
        for tid in unlocked:
            submit_solution(client, tid, curriculum.get_task(tid)["solution"])
    # 天劫
    for wave in sorted(curriculum.tribulation_waves().values(), key=lambda w: w["order"]):
        t = curriculum.get_task(wave["task"])
        submit_solution(client, t["id"], t["solution"])
    resp = client.post("/api/breakthrough")
    data = resp.get_json()
    assert data["event"]["founded"] is True
    ids = [a["id"] for a in data["new_achievements"]]
    assert "foundation" in ids
    assert data["state"]["player"]["title"] == "筑基真人"
