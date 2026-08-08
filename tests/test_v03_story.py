# -*- coding: utf-8 -*-
"""V0.3-D 章节、宗门任务与随机奇遇验收。"""

import random

from game import curriculum, server, story
from game.player import Player


def test_story_content_counts_and_task_links():
    data = story.story_data()
    assert len(data["chapters"]) >= 3
    assert len(data["sect_quests"]) >= 5
    assert len(data["encounters"]) >= 8
    task_ids = set(curriculum.all_tasks())
    for chapter in data["chapters"]:
        for node in chapter["nodes"]:
            assert node["task_id"] in task_ids


def test_all_quest_and_encounter_solutions_pass_sandbox():
    for quest_id in story.story_data()["sect_quests"]:
        quest = story.get_quest(quest_id)
        assert story.validate_item(quest, quest["challenge"]["solution"], "sect").passed
    for encounter_id in story.story_data()["encounters"]:
        encounter = story.get_encounter(encounter_id)
        assert story.validate_item(encounter, encounter["challenge"]["solution"], "encounter").passed


def test_sect_quest_rewards_only_after_valid_code():
    player = Player()
    failed, reward = story.submit_quest(player, "sect_patrol", "print('wrong')")
    assert failed.passed is False and reward == {}
    quest = story.get_quest("sect_patrol")
    passed, reward = story.submit_quest(player, "sect_patrol", quest["challenge"]["solution"])
    assert passed.passed is True
    assert reward["sect_contribution"] == 10
    assert "sect_patrol" in player.branch_completed


def test_encounter_trigger_persists_and_clear_adds_log():
    player = Player(world_location="encounter_site")
    encounter = story.trigger_encounter(player, "encounter_site", random.Random(7))
    assert player.story_flags[story.ACTIVE_ENCOUNTER_FLAG] == encounter["id"]
    failed, reward = story.submit_encounter(player, encounter["id"], "print('wrong')")
    assert failed.passed is False and reward == {}
    passed, reward = story.submit_encounter(player, encounter["id"], encounter["challenge"]["solution"])
    assert passed.passed is True
    assert encounter["id"] in player.encounter_log
    assert story.ACTIVE_ENCOUNTER_FLAG not in player.story_flags


def test_story_fields_roundtrip():
    player = Player(story_flags={"chapter": "two"}, sect_contribution=33, encounter_log=["lost_scroll"])
    restored = Player.from_dict(player.to_dict())
    assert restored.story_flags == {"chapter": "two"}
    assert restored.sect_contribution == 33
    assert restored.encounter_log == ["lost_scroll"]


def test_story_api_quest_and_encounter_flow(client, new_player):
    server._current_player.realm_key = "qi5"
    server._current_player.world_location = "mission_hall"
    quest = story.get_quest("sect_archive")
    response = client.post("/api/story/quests/sect_archive/submit", json={"code": quest["challenge"]["solution"]})
    assert response.status_code == 200
    assert response.get_json()["outcome"]["passed"] is True

    server._current_player.world_location = "encounter_site"
    triggered = client.post("/api/story/encounters/trigger")
    assert triggered.status_code == 200
    encounter_id = triggered.get_json()["encounter"]["id"]
    encounter = story.get_encounter(encounter_id)
    cleared = client.post("/api/story/encounters/%s/submit" % encounter_id, json={"code": encounter["challenge"]["solution"]})
    assert cleared.status_code == 200
    assert cleared.get_json()["outcome"]["passed"] is True
