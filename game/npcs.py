# -*- coding: utf-8 -*-
"""NPC 注册表、地点绑定、好感度与关系称谓。"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DEFAULT_RELATIONSHIPS = (
    (80, "莫逆"),
    (40, "相知"),
    (15, "相识"),
    (0, "陌生"),
)


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("npcs.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "npcs.json"), "r", encoding="utf-8-sig") as handle:
            return json.load(handle)


@lru_cache(maxsize=1)
def npcs() -> dict:
    return _load()["npcs"]


def get_npc(npc_id: str) -> dict | None:
    return npcs().get(npc_id)


def relationship_name(npc: dict, affinity: int) -> str:
    levels = npc.get("relationship") or [
        {"min": minimum, "name": name} for minimum, name in reversed(_DEFAULT_RELATIONSHIPS)
    ]
    ordered = sorted(levels, key=lambda item: int(item.get("min", 0)), reverse=True)
    for level in ordered:
        if affinity >= int(level.get("min", 0)):
            return level.get("name", "陌生")
    return "陌生"


def for_player(player, npc_id: str) -> dict | None:
    npc = get_npc(npc_id)
    if npc is None:
        return None
    item = dict(npc, id=npc_id)
    affinity = player.npc_affinity_for(npc_id) if player is not None else int(npc.get("affinity", 0))
    item["affinity"] = affinity
    item["relationship_name"] = relationship_name(npc, affinity)
    item["present"] = bool(player is not None and player.world_location == npc.get("location"))
    return item


def all_npcs(player=None) -> list[dict]:
    return [for_player(player, npc_id) for npc_id in npcs()]
