# -*- coding: utf-8 -*-
"""NPC 系统：NPC 注册表（数据驱动，game/data/npcs.json）。"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("npcs.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "npcs.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def npcs() -> dict:
    return _load()["npcs"]


def get_npc(npc_id: str) -> dict | None:
    return npcs().get(npc_id)


def all_npcs() -> list[dict]:
    return [dict(npc, id=npc_id) for npc_id, npc in npcs().items()]
