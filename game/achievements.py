# -*- coding: utf-8 -*-
"""成就系统：数据驱动（game/data/achievements.json）+ 条件引擎。

条件类型：
    task_done       {task_id}                主线任务完成
    realm_reached  {realm_key}               境界（含该境界）到达
    count          {field, op, value}        列表字段数量比较（op: >= > ==）
    cultivation_ge {value}                   修为达到
    debug_exp_ge   {value}                   除魔经验达到
    streak_ge      {value}                   连续通过次数
    items_ge       {value}                   道具总数
    flag           {key}                     玩家布尔字段（如 founded）
    event          {flag}                    上下文事件标记（如 item_used）
    secret_cleared {realm_id}                秘境通关次数 >= 1
    secret_count_ge {value}                  秘境累计通关次数

解锁时自动发放奖励并授予称号。
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_LIST_FIELDS = {
    "completed_tasks": lambda p: p.completed_tasks,
    "debug_completed": lambda p: p.debug_completed,
    "branch_completed": lambda p: p.branch_completed,
    "tribulation_passed": lambda p: p.tribulation_passed,
    "techniques": lambda p: p.techniques,
    "achievements": lambda p: p.achievements,
}


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("achievements.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "achievements.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def achievements() -> dict:
    return _load()["achievements"]


def get_achievement(ach_id: str) -> dict | None:
    return achievements().get(ach_id)


def _check_condition(player, cond: dict, context: dict) -> bool:
    ctype = cond.get("type", "")
    if ctype == "task_done":
        return cond.get("task_id") in player.completed_tasks
    if ctype == "realm_reached":
        from . import curriculum
        target = curriculum.realm_order(cond.get("realm_key", ""))
        return target >= 0 and curriculum.realm_order(player.realm_key) >= target
    if ctype == "count":
        field = cond.get("field", "")
        getter = _LIST_FIELDS.get(field)
        if not getter:
            return False
        value = len(getter(player))
        op = cond.get("op", ">=")
        return {"==": value == cond["value"], ">": value > cond["value"], ">=": value >= cond["value"]}.get(op, False)
    if ctype == "cultivation_ge":
        return player.cultivation >= cond.get("value", 0)
    if ctype == "debug_exp_ge":
        return player.debug_exp >= cond.get("value", 0)
    if ctype == "streak_ge":
        return player.streak >= cond.get("value", 0)
    if ctype == "items_ge":
        return sum(player.items.values()) >= cond.get("value", 0)
    if ctype == "flag":
        return bool(getattr(player, cond.get("key", ""), False))
    if ctype == "event":
        return bool(context.get(cond.get("flag", "")))
    if ctype == "secret_cleared":
        return player.secret_log.get(cond.get("realm_id", ""), 0) >= 1
    if ctype == "secret_count_ge":
        return sum(player.secret_log.values()) >= cond.get("value", 0)
    return False


def _apply_reward(player, reward: dict) -> dict:
    details = {}
    if reward.get("cultivation"):
        player.add_cultivation(int(reward["cultivation"]))
        details["cultivation"] = int(reward["cultivation"])
    if reward.get("comprehension"):
        player.add_comprehension(int(reward["comprehension"]))
        details["comprehension"] = int(reward["comprehension"])
    if reward.get("debug_exp"):
        player.add_debug_exp(int(reward["debug_exp"]))
        details["debug_exp"] = int(reward["debug_exp"])
    if reward.get("mindset"):
        player.add_mindset(int(reward["mindset"]))
        details["mindset"] = int(reward["mindset"])
    for item_id in reward.get("items", []):
        player.add_item(item_id)
        details.setdefault("items", []).append(item_id)
    return details


def check_all(player, context: dict | None = None) -> list[dict]:
    """检查全部成就，返回本次新解锁的成就（已自动发奖）。"""
    context = context or {}
    unlocked = []
    for ach_id, ach in achievements().items():
        if ach_id in player.achievements:
            continue
        if _check_condition(player, ach.get("condition", {}), context):
            player.unlock_achievement(ach_id)
            reward = _apply_reward(player, ach.get("reward", {}))
            title = ach.get("title", "")
            if title:
                player.title = title
            unlocked.append({"id": ach_id, "name": ach["name"], "icon": ach.get("icon", "🏅"), "desc": ach["desc"], "reward": reward, "title": title})
    return unlocked


def all_with_status(player) -> list[dict]:
    result = []
    for ach_id, ach in achievements().items():
        result.append(dict(ach, id=ach_id, unlocked=ach_id in player.achievements))
    return result
