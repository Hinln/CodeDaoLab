# -*- coding: utf-8 -*-
"""道具系统：道具注册表与使用逻辑。

道具定义见 game/data/items.json（数据驱动）。
使用道具通过 effect 描述符应用效果，消费对应数量。
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_items() -> dict:
    try:
        text = resources.files("game.data").joinpath("items.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "items.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def items() -> dict:
    return _load_items()["items"]


def get_item(item_id: str) -> dict | None:
    return items().get(item_id)


def use_item(player, item_id: str) -> dict:
    """使用道具，返回 {used, message, effect}；未拥有或不可用返回 used=False。"""
    item = get_item(item_id)
    if item is None:
        return {"used": False, "message": "不存在的道具。"}
    if not player.has_item(item_id):
        return {"used": False, "message": "尚未获得「%s」。" % item["name"]}
    effect = item.get("effect", {})
    for key, value in effect.items():
        if key == "mindset":
            player.add_mindset(int(value))
        elif key == "comprehension":
            player.add_comprehension(int(value))
        elif key == "debug_exp":
            player.add_debug_exp(int(value))
        elif key == "cultivation":
            player.add_cultivation(int(value))
    player.consume_item(item_id)
    return {
        "used": True,
        "message": "服下「%s」，%s" % (item["name"], item["desc"]),
        "effect": effect,
    }
