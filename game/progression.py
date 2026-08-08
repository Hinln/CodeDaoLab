# -*- coding: utf-8 -*-
"""V0.3 长期成长总览：贡献、图鉴、关系与自由目标（只读）。"""

from __future__ import annotations

from . import curriculum, npcs, story, tasks, techniques

CORE_NPCS = ("master_qingxuan", "elder_library", "guide_realm", "sect_master")


def _objectives(player, technique_items: list[dict], encounter_items: list[dict], relation_items: list[dict]) -> list[dict]:
    result = []
    current_id = tasks.current_task_id(player)
    current = curriculum.get_task(current_id) if current_id else None
    if current:
        result.append({"id": "main", "type": "主线", "title": current.get("title", "继续修行"), "desc": "完成当前真实代码任务，推动境界与章节。", "location": "dormitory"})

    practice = next((item for item in technique_items if item["unlocked"] and item["level"] < 4), None)
    if practice:
        result.append({"id": "practice", "type": "功法", "title": "修炼" + practice["title"], "desc": "在演武场通过代码挑战提升熟练度与等级。", "location": "training_ground"})

    undiscovered = [item for item in encounter_items if not item["discovered"]]
    if undiscovered:
        result.append({"id": "explore", "type": "探索", "title": "寻找未知奇遇", "desc": "尚有 %d 种奇遇未收入图鉴。" % len(undiscovered), "location": "encounter_site"})

    relation = min(relation_items, key=lambda item: item["affinity"], default=None)
    if relation and relation["affinity"] < 80:
        result.append({"id": "relationship", "type": "关系", "title": "拜访" + relation["name"], "desc": "前往其所在地点，通过对话与真实任务推进关系。", "location": relation["location"]})

    incomplete_quests = [quest for quest in story.summarize(player)["sect_quests"] if not quest["completed"]]
    if incomplete_quests:
        result.append({"id": "sect", "type": "宗门", "title": "完成宗门委托", "desc": "任务堂尚有 %d 项代码委托。" % len(incomplete_quests), "location": "mission_hall"})
    return result


def summarize(player) -> dict:
    technique_items = techniques.summarize(player)
    encounter_items = []
    for encounter_id in story.story_data()["encounters"]:
        encounter = story.get_encounter(encounter_id)
        encounter_items.append({
            "id": encounter_id,
            "title": encounter["title"],
            "discovered": encounter_id in player.encounter_log,
        })
    relation_items = []
    for npc_id in CORE_NPCS:
        npc = npcs.for_player(player, npc_id)
        if npc:
            relation_items.append({
                "id": npc_id,
                "name": npc["name"],
                "location": npc["location"],
                "affinity": npc["affinity"],
                "relationship": npc["relationship_name"],
            })
    learned = [item for item in technique_items if item["unlocked"]]
    mastered = [item for item in learned if item["level"] >= 4]
    discovered = [item for item in encounter_items if item["discovered"]]
    return {
        "sect_contribution": player.sect_contribution,
        "technique_codex": technique_items,
        "encounter_codex": encounter_items,
        "relationships": relation_items,
        "objectives": _objectives(player, technique_items, encounter_items, relation_items),
        "stats": {
            "techniques_learned": len(learned),
            "techniques_total": len(technique_items),
            "techniques_mastered": len(mastered),
            "encounters_discovered": len(discovered),
            "encounters_total": len(encounter_items),
        },
    }
