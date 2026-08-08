# -*- coding: utf-8 -*-
"""V0.3-E 长期成长聚合与自由目标验收。"""

from game import progression, story, techniques, world
from game.player import Player


def test_progression_contains_all_long_term_systems():
    player = Player(techniques=["mortal"])
    data = progression.summarize(player)
    assert data["sect_contribution"] == 0
    assert len(data["technique_codex"]) >= 12
    assert len(data["encounter_codex"]) >= 8
    assert len(data["relationships"]) == 4
    assert {item["type"] for item in data["objectives"]} >= {"主线", "功法", "探索", "关系", "宗门"}


def test_progression_reflects_growth_state():
    player = Player(techniques=["mortal"], sect_contribution=25, encounter_log=["lost_scroll"])
    player.technique_level["mortal"] = 4
    player.technique_progress["mortal"] = 100
    player.npc_affinity["master_qingxuan"] = 42
    data = progression.summarize(player)
    assert data["stats"]["techniques_mastered"] == 1
    assert data["stats"]["encounters_discovered"] == 1
    master = next(item for item in data["relationships"] if item["id"] == "master_qingxuan")
    assert master["affinity"] == 42


def test_free_objectives_point_to_valid_world_locations():
    player = Player(techniques=["mortal"])
    location_ids = {loc["id"] for region in world.world_data()["regions"] for loc in region["locations"]}
    assert all(item["location"] in location_ids for item in progression.summarize(player)["objectives"])


def test_progression_summary_is_read_only():
    player = Player(techniques=["mortal"])
    before = player.to_dict()
    progression.summarize(player)
    assert player.to_dict() == before


def test_progression_api(client, new_player):
    response = client.get("/api/progression")
    assert response.status_code == 200
    data = response.get_json()["progression"]
    assert data["stats"]["techniques_total"] == len(techniques.all_techniques())
    assert data["stats"]["encounters_total"] == len(story.story_data()["encounters"])
