# -*- coding: utf-8 -*-
"""V0.3-A 世界地图与存档迁移验收。"""

from __future__ import annotations

import json

from game import save, world
from game.player import Player


def _all_locations() -> list[dict]:
    return [location for region in world.world_data()["regions"] for location in region["locations"]]


def test_world_has_three_regions_and_twelve_locations():
    data = world.world_data()
    assert len(data["regions"]) >= 3
    assert len(_all_locations()) >= 12
    assert {r["id"] for r in data["regions"]} >= {"qingyun_sect", "qingyun_city", "back_mountain"}


def test_world_connections_are_valid_and_symmetric():
    locations = {location["id"]: location for location in _all_locations()}
    assert len(locations) == len(_all_locations())
    for location_id, location in locations.items():
        assert isinstance(location.get("x"), int)
        assert isinstance(location.get("y"), int)
        assert location.get("connections")
        for target_id in location["connections"]:
            assert target_id in locations
            assert location_id in locations[target_id]["connections"]


def test_world_summary_marks_only_adjacent_locations_reachable():
    summary = world.summarize(Player())
    by_id = {location["id"]: location for location in summary["locations"]}
    assert summary["current_location"] == "dormitory"
    assert by_id["gate"]["reachable"] is True
    assert by_id["dormitory"]["current"] is True
    assert by_id["city_gate"]["reachable"] is False
    assert by_id["market"]["reachable"] is False


def test_world_move_checks_unlock_and_connection():
    player = Player()
    assert world.location_entry_status(player, "gate") == (True, "")
    assert world.location_entry_status(player, "market")[0] is False
    player.world_location = "gate"
    allowed, reason = world.location_entry_status(player, "city_gate")
    assert allowed is False
    assert reason
    player.realm_key = "qi3"
    assert world.location_entry_status(player, "city_gate") == (True, "")


def test_world_api_move_and_connection_gate(client, new_player):
    moved = client.post("/api/world/move", json={"location_id": "gate"})
    assert moved.status_code == 200
    assert moved.get_json()["world"]["current_location"] == "gate"
    blocked = client.post("/api/world/move", json={"location_id": "market"})
    assert blocked.status_code == 403


def test_save_version_three_and_v2_compatibility(app):
    player = Player(name="迁移测试", world_location="gate")
    save.save_game(player, "v3_world")
    with open(save._slot_path("v3_world"), "r", encoding="utf-8") as handle:
        assert json.load(handle)["version"] == 3
    legacy_path = save._slot_path("v2_world")
    with open(legacy_path, "w", encoding="utf-8") as handle:
        json.dump({"version": 2, "player": {"name": "旧档"}}, handle, ensure_ascii=False)
    loaded = save.load_game("v2_world")
    assert loaded is not None
    assert loaded.world_location == "dormitory"
