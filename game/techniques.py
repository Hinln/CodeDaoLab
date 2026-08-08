# -*- coding: utf-8 -*-
"""V0.3 功法系统：独立数据、熟练度、等级、功法树与代码考核。"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LEVEL_NAMES = {1: "入门", 2: "小成", 3: "大成", 4: "圆满"}
LEVEL_THRESHOLDS = {1: 0, 2: 40, 3: 70, 4: 100}


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("techniques.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "techniques.json"), "r", encoding="utf-8-sig") as handle:
            return json.load(handle)


@lru_cache(maxsize=1)
def technique_data() -> dict:
    return _load()


def all_techniques() -> list[dict]:
    return [dict(item, id=technique_id) for technique_id, item in technique_data()["techniques"].items()]


def get_technique(technique_id: str) -> dict | None:
    item = technique_data()["techniques"].get(technique_id)
    return dict(item, id=technique_id) if item else None


def techniques_for_realm(realm_key: str) -> list[dict]:
    return [item for item in all_techniques() if item.get("realm_key") == realm_key]


def technique_for_realm(realm: dict) -> dict | None:
    """兼容 V0.2：返回该境界首门功法。"""
    found = techniques_for_realm(realm.get("key", ""))
    return found[0] if found else None


def learn_realm_technique(player, realm_key: str) -> bool:
    learned = False
    for technique in techniques_for_realm(realm_key):
        if technique["id"] not in player.techniques:
            player.learn_technique(technique["id"])
            learned = True
        player.technique_progress.setdefault(technique["id"], 0)
        player.technique_level.setdefault(technique["id"], 1)
    return learned


def tree_requirement_met(player, technique: dict) -> bool:
    for prereq in technique.get("prereq", []):
        if int(player.technique_level.get(prereq["id"], 1 if prereq["id"] in player.techniques else 0)) < int(prereq.get("level", 1)):
            return False
    return True


def add_progress(player, technique_id: str, amount: int) -> int:
    if technique_id not in player.techniques:
        return 0
    current = int(player.technique_progress.get(technique_id, 0))
    updated = max(0, min(100, current + int(amount)))
    player.technique_progress[technique_id] = updated
    player.technique_level.setdefault(technique_id, 1)
    return updated - current


def award_task_progress(player, amount: int = 20) -> dict[str, int]:
    gained = {}
    candidates = techniques_for_realm(player.realm_key)
    for technique in candidates:
        delta = add_progress(player, technique["id"], amount)
        if delta:
            gained[technique["id"]] = delta
    return gained


def challenge_for(technique_id: str) -> dict | None:
    technique = get_technique(technique_id)
    if not technique:
        return None
    return dict(technique.get("challenge") or {})


def validate_challenge(technique_id: str, code: str):
    from . import tasks

    challenge = challenge_for(technique_id)
    if not challenge:
        return None
    task = dict(challenge, id="practice:" + technique_id, kind="practice")
    check = dict(task.get("check") or {})
    if isinstance(check.get("expected"), str):
        check["expected"] = {"exact": check["expected"]}
    task["check"] = check
    return tasks.validate_task(task, code)


def can_exam(player, technique_id: str) -> bool:
    if technique_id not in player.techniques:
        return False
    level = int(player.technique_level.get(technique_id, 1))
    if level >= 4:
        return False
    return int(player.technique_progress.get(technique_id, 0)) >= LEVEL_THRESHOLDS[level + 1]


def complete_exam(player, technique_id: str) -> int:
    if not can_exam(player, technique_id):
        raise ValueError("熟练度尚未达到下一境界要求。")
    level = min(4, int(player.technique_level.get(technique_id, 1)) + 1)
    player.technique_level[technique_id] = level
    if level == 3:
        player.add_comprehension(1)
    return level


def summarize(player) -> list[dict]:
    result = []
    for technique in all_techniques():
        unlocked = technique["id"] in player.techniques
        level = int(player.technique_level.get(technique["id"], 1 if unlocked else 0))
        progress = int(player.technique_progress.get(technique["id"], 0))
        item = dict(technique)
        item.pop("challenge", None)
        item.update({
            "unlocked": unlocked,
            "level": level,
            "level_name": LEVEL_NAMES.get(level, "未习得"),
            "progress": progress,
            "tree_unlocked": tree_requirement_met(player, technique),
            "can_exam": can_exam(player, technique["id"]),
            "next_threshold": LEVEL_THRESHOLDS.get(level + 1),
        })
        result.append(item)
    return result


def public_challenge(technique_id: str) -> dict | None:
    challenge = challenge_for(technique_id)
    if not challenge:
        return None
    return {key: challenge.get(key) for key in ("title", "story", "starter_code")}
