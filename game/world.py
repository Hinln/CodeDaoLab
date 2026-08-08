# -*- coding: utf-8 -*-
"""世界地图模块：加载世界配置、计算解锁状态，并提供可进出地点的判定。"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

from . import curriculum, npcs


_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("world.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "world.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def world_data() -> dict:
    return _load()


def _find_region(region_id: str) -> dict | None:
    if not region_id:
        return None
    for region in world_data().get("regions", []):
        if region.get("id") == region_id:
            return region
    return None


def _find_location(location_id: str) -> tuple[dict | None, dict | None]:
    for region in world_data().get("regions", []):
        for loc in region.get("locations", []):
            if loc.get("id") == location_id:
                return loc, region
    return None, None


def _cond_realm_order_min(player, cond: dict) -> bool:
    need_order = int(cond.get("order", 0))
    return curriculum.realm_order(player.realm_key) >= need_order


def _cond_has_done_task(player, cond: dict) -> bool:
    task_id = cond.get("task_id", "")
    if not task_id:
        return False
    return (
        task_id in player.completed_tasks
        or task_id in player.debug_completed
        or task_id in player.branch_completed
    )


def _cond_world_location(player, cond: dict) -> bool:
    target = (cond.get("location") or "").strip()
    if not target:
        return False
    return player.world_location == target


def _cond_eval(player, cond: dict | None) -> bool:
    if not cond:
        return True
    cond_type = cond.get("type", "always")
    if cond_type == "always":
        return True
    if cond_type == "realm_order_min":
        return _cond_realm_order_min(player, cond)
    if cond_type == "task_done":
        return _cond_has_done_task(player, cond)
    if cond_type == "world_location":
        return _cond_world_location(player, cond)
    if cond_type == "and":
        return all(_cond_eval(player, c) for c in cond.get("conditions", []))
    if cond_type == "or":
        return any(_cond_eval(player, c) for c in cond.get("conditions", []))
    return False


def _cond_reason(cond: dict | None) -> str:
    if not cond:
        return "未满足解锁条件"
    cond_type = cond.get("type", "always")
    if cond_type == "always":
        return ""
    if cond_type == "realm_order_min":
        return "需达到" + str(int(cond.get("order", 0))) + "重境界"
    if cond_type == "task_done":
        task_id = cond.get("task_id", "")
        if not task_id:
            return "需先完成指定机缘"
        return "需先完成任务：" + task_id
    if cond_type == "world_location":
        target = (cond.get("location") or "").strip()
        return "需先到达：" + (target or "指定区域")
    if cond_type == "and":
        return "需同时满足多项条件"
    if cond_type == "or":
        return "需满足任一条件"
    return "未满足解锁条件"


def _location_unlocked(player, location: dict, region: dict | None = None) -> tuple[bool, str]:
    if region is None:
        region = {"unlock": {"type": "always"}, "name": "所在区域"}

    region_open = _cond_eval(player, region.get("unlock"))
    if not region_open:
        return False, region.get("name", "所在区域") + "尚未开启"

    if _cond_eval(player, location.get("unlock")):
        return True, ""

    reason = location.get("locked_reason", "")
    return False, reason or _cond_reason(location.get("unlock"))


def _effective_location(player) -> tuple[str, dict | None, dict | None]:
    """返回可用的当前位置；旧档坐标失效时回退到洞府。"""
    location_id = player.world_location or "dormitory"
    location, region = _find_location(location_id)
    if location is not None and _location_unlocked(player, location, region)[0]:
        return location_id, location, region

    fallback, fallback_region = _find_location("dormitory")
    if fallback is not None and _location_unlocked(player, fallback, fallback_region)[0]:
        return "dormitory", fallback, fallback_region

    for candidate_region in world_data().get("regions", []):
        for candidate in candidate_region.get("locations", []):
            if _location_unlocked(player, candidate, candidate_region)[0]:
                return candidate.get("id", ""), candidate, candidate_region
    return "", None, None


def summarize(player) -> dict:
    """返回当前玩家可见的世界地图状态。"""
    regions: list[dict] = []
    unlocked_locations: dict[str, bool] = {}
    all_locations: list[dict] = []

    for region in world_data().get("regions", []):
        reg_unlocked = _cond_eval(player, region.get("unlock"))
        loc_list = []
        for loc in region.get("locations", []):
            loc_item = dict(loc)
            loc_id = loc_item.get("id")
            is_open, reason = _location_unlocked(player, loc, region)
            loc_item["unlocked"] = bool(reg_unlocked and is_open)
            loc_item["locked_reason"] = reason
            loc_item["region_id"] = region.get("id")
            loc_item["region_name"] = region.get("name", "")
            loc_list.append(loc_item)
            unlocked_locations[loc_id] = loc_item["unlocked"]
            all_locations.append(loc_item)

        regions.append({
            "id": region.get("id"),
            "name": region.get("name", ""),
            "desc": region.get("desc", ""),
            "unlocked": bool(reg_unlocked),
            "locations": loc_list,
        })

    current_location, loc_def, region_def = _effective_location(player)
    connected = set((loc_def or {}).get("connections", []))
    for loc in all_locations:
        loc_id = loc.get("id", "")
        loc["current"] = loc_id == current_location
        loc["reachable"] = bool(
            loc.get("unlocked") and (loc_id == current_location or loc_id in connected)
        )
        loc["move_reason"] = (
            "需从相邻地点前往"
            if loc.get("unlocked") and not loc["reachable"]
            else ""
        )

    current_region = region_def["id"] if region_def else (regions[0]["id"] if regions else "")
    location_npcs = []
    for npc in npcs.all_npcs(player):
        location_npcs.append({
            "id": npc.get("id", ""),
            "name": npc.get("name", ""),
            "location": npc.get("location", ""),
            "title": npc.get("title", ""),
            "icon": npc.get("icon", "🧙"),
            "affinity": npc.get("affinity", 0),
            "relationship": npc.get("relationship_name", "陌生"),
            "present": npc.get("present", False),
        })

    return {
        "current_region": current_region,
        "current_location": current_location,
        "regions": regions,
        "locations": all_locations,
        "npcs": location_npcs,
        "location_unlocked": unlocked_locations,
    }


def location_can_enter(player, location_id: str) -> bool:
    """兼容旧调用：目标必须解锁且与当前位置直接相连。"""
    return location_entry_status(player, location_id)[0]


def location_entry_status(player, location_id: str) -> tuple[bool, str]:
    """检查一次地图移动，返回是否允许及面向玩家的原因。"""
    loc, region = _find_location(location_id)
    if loc is None:
        return False, "地点不存在"
    opened, reason = _location_unlocked(player, loc, region)
    if not opened:
        return False, reason or "该地点尚未开辟"

    current_id, current, _ = _effective_location(player)
    if not current:
        return False, "当前所在地点无效"
    if location_id == current_id:
        return True, ""
    if location_id not in current.get("connections", []):
        return False, "两地并不直接相连"
    return True, ""
