# -*- coding: utf-8 -*-
"""V0.3-B NPC 地点、好感度、关系与专属对话验收。"""

from game import dialogues, npcs, world
from game.player import Player


CORE_NPCS = {"master_qingxuan", "guide_realm", "elder_library", "sect_master"}


def test_core_npcs_have_world_locations_and_relationships():
    location_ids = {loc["id"] for region in world.world_data()["regions"] for loc in region["locations"]}
    npc_map = {npc["id"]: npc for npc in npcs.all_npcs()}
    assert CORE_NPCS <= set(npc_map)
    for npc_id in CORE_NPCS:
        assert npc_map[npc_id]["location"] in location_ids
        assert len(npc_map[npc_id]["relationship"]) >= 4
        assert dialogues.get_tree(npc_id)


def test_affinity_clamps_and_roundtrips():
    player = Player()
    assert player.add_npc_affinity("master_qingxuan", 120) == 100
    assert player.add_npc_affinity("master_qingxuan", -150) == 0
    restored = Player.from_dict(player.to_dict())
    assert restored.npc_affinity == {"master_qingxuan": 0}


def test_dialogue_affinity_is_idempotent_and_updates_relationship():
    player = Player()
    first = dialogues.choose(player, "master_qingxuan", "start", 1)
    second = dialogues.choose(player, "master_qingxuan", "start", 1)
    assert first["affinity"] == 5
    assert second["affinity"] == 5
    assert player.npc_affinity_for("master_qingxuan") == 5
    assert any("好感+5" in effect for effect in first["effects"])


def test_affinity_unlocks_exclusive_story_option():
    player = Player()
    locked = dialogues.enter(player, "master_qingxuan")
    assert all("过往" not in option["text"] for option in locked["options"])
    player.npc_affinity["master_qingxuan"] = 60
    unlocked = dialogues.enter(player, "master_qingxuan")
    assert any("过往" in option["text"] for option in unlocked["options"])


def test_world_binds_npcs_to_locations():
    player = Player(world_location="dormitory")
    summary = world.summarize(player)
    npc_map = {npc["id"]: npc for npc in summary["npcs"]}
    assert npc_map["master_qingxuan"]["location"] == "dormitory"
    assert npc_map["master_qingxuan"]["present"] is True
    assert npc_map["elder_library"]["present"] is False


def test_npc_api_and_dialogue_return_affinity(client, new_player):
    npc_data = client.get("/api/npcs").get_json()["npcs"]
    master = next(npc for npc in npc_data if npc["id"] == "master_qingxuan")
    assert master["location"] == "dormitory"
    assert master["affinity"] == 0
    result = client.post("/api/dialogues/master_qingxuan/choose", json={"node_id": "start", "option_index": 1}).get_json()
    assert result["dialogue"]["affinity"] == 5
    assert result["state"]["player"]["npc_affinity"]["master_qingxuan"] == 5
