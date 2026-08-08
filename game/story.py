# -*- coding: utf-8 -*-
"""V0.3 章节、宗门支线与随机奇遇系统。"""

from __future__ import annotations

import json
import os
import random
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ACTIVE_ENCOUNTER_FLAG = "active_encounter"


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("story.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "story.json"), "r", encoding="utf-8-sig") as handle:
            return json.load(handle)


@lru_cache(maxsize=1)
def story_data() -> dict:
    return _load()


def get_quest(quest_id: str) -> dict | None:
    item = story_data()["sect_quests"].get(quest_id)
    return dict(item, id=quest_id) if item else None


def get_encounter(encounter_id: str) -> dict | None:
    item = story_data()["encounters"].get(encounter_id)
    return dict(item, id=encounter_id) if item else None


def _public_challenge(item: dict) -> dict:
    challenge = item.get("challenge") or {}
    return {
        "id": item["id"],
        "title": item.get("title", ""),
        "story": item.get("story", ""),
        "starter_code": challenge.get("starter_code", ""),
    }


def _validation_task(item: dict, kind: str) -> dict:
    challenge = dict(item.get("challenge") or {})
    check = dict(challenge.get("check") or {})
    if isinstance(check.get("expected"), str):
        check["expected"] = {"exact": check["expected"]}
    challenge["check"] = check
    challenge["id"] = "%s:%s" % (kind, item["id"])
    challenge["kind"] = kind
    return challenge


def validate_item(item: dict, code: str, kind: str):
    from . import tasks

    return tasks.validate_task(_validation_task(item, kind), code)


def _apply_reward(player, reward: dict) -> dict:
    details = {}
    cultivation = int(reward.get("cultivation", 0))
    contribution = int(reward.get("sect_contribution", 0))
    if cultivation:
        player.add_cultivation(cultivation)
        details["cultivation"] = cultivation
    if contribution:
        player.sect_contribution += contribution
        details["sect_contribution"] = contribution
    return details


def submit_quest(player, quest_id: str, code: str):
    quest = get_quest(quest_id)
    if quest is None:
        raise ValueError("宗门任务不存在。")
    if quest_id in player.branch_completed:
        raise ValueError("该宗门任务已经完成。")
    outcome = validate_item(quest, code, "sect")
    reward = {}
    if outcome.passed:
        player.branch_completed.append(quest_id)
        player.story_flags["quest:" + quest_id] = "completed"
        reward = _apply_reward(player, quest.get("reward") or {})
    return outcome, reward


def trigger_encounter(player, location_id: str, rng=None) -> dict:
    active_id = player.story_flags.get(ACTIVE_ENCOUNTER_FLAG)
    if active_id:
        active = get_encounter(active_id)
        if active:
            return active
    candidates = [
        item for item in (get_encounter(encounter_id) for encounter_id in story_data()["encounters"])
        if location_id in item.get("locations", []) and item["id"] not in player.encounter_log
    ]
    if not candidates:
        candidates = [
            item for item in (get_encounter(encounter_id) for encounter_id in story_data()["encounters"])
            if location_id in item.get("locations", [])
        ]
    if not candidates:
        raise ValueError("此地暂无线索。")
    chosen = (rng or random).choice(candidates)
    player.story_flags[ACTIVE_ENCOUNTER_FLAG] = chosen["id"]
    return chosen


def submit_encounter(player, encounter_id: str, code: str):
    encounter = get_encounter(encounter_id)
    if encounter is None:
        raise ValueError("奇遇不存在。")
    if player.story_flags.get(ACTIVE_ENCOUNTER_FLAG) != encounter_id:
        raise ValueError("当前并未遭遇此事。")
    outcome = validate_item(encounter, code, "encounter")
    reward = {}
    if outcome.passed:
        if encounter_id not in player.encounter_log:
            player.encounter_log.append(encounter_id)
        player.story_flags["encounter:" + encounter_id] = "completed"
        player.story_flags.pop(ACTIVE_ENCOUNTER_FLAG, None)
        reward = _apply_reward(player, encounter.get("reward") or {})
    return outcome, reward


def summarize(player) -> dict:
    completed = set(player.completed_tasks + player.debug_completed + player.branch_completed)
    chapters = []
    for chapter in story_data()["chapters"]:
        nodes = [dict(node, completed=node.get("task_id") in completed) for node in chapter.get("nodes", [])]
        chapters.append(dict(chapter, nodes=nodes, completed=bool(nodes) and all(node["completed"] for node in nodes)))
    quests = []
    for quest_id in story_data()["sect_quests"]:
        quest = get_quest(quest_id)
        public = _public_challenge(quest)
        public["completed"] = quest_id in player.branch_completed
        public["reward"] = quest.get("reward", {})
        quests.append(public)
    active_id = player.story_flags.get(ACTIVE_ENCOUNTER_FLAG, "")
    active = get_encounter(active_id) if active_id else None
    return {
        "chapters": chapters,
        "sect_quests": quests,
        "active_encounter": _public_challenge(active) if active else None,
        "encounter_log": list(player.encounter_log),
        "encounter_total": len(story_data()["encounters"]),
        "sect_contribution": player.sect_contribution,
    }


def public_quest(quest_id: str) -> dict | None:
    quest = get_quest(quest_id)
    return _public_challenge(quest) if quest else None


def public_encounter(encounter: dict) -> dict:
    return _public_challenge(encounter)
