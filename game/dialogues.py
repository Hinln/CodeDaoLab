# -*- coding: utf-8 -*-
"""对话系统：节点式对话树（数据驱动，game/data/dialogues.json）。

节点结构：
    { "id": { "text": "...", "actions": [...], "options": [{"text": "...", "goto": "..."}] } }

动作类型（进入节点时执行，按 action id 对每个玩家只生效一次）：
    reward          {cultivation/comprehension/mindset/debug_exp/item/achievement}
    unlock_task     {task_id}            解锁支线任务
    unlock_secret   {secret_id}          解锁秘境
    learn_technique {technique_id}       习得功法
    affinity        {value, npc_id?}     调整 NPC 好感度
    flag            {key}                记录剧情标记（风味）
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

from . import curriculum, items as items_mod, npcs as npcs_mod

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

END_NODE = "__end__"


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("dialogues.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "dialogues.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def dialogues() -> dict:
    return _load()


def get_tree(npc_id: str) -> dict | None:
    return dialogues().get(npc_id)


def start_node_id(npc_id: str) -> str:
    tree = get_tree(npc_id) or {}
    return "start" if "start" in tree else (next(iter(tree), END_NODE))


def get_node(npc_id: str, node_id: str) -> dict | None:
    tree = get_tree(npc_id) or {}
    return tree.get(node_id)


def _require_met(player, npc_id: str, require: dict | None) -> bool:
    if not require:
        return True
    if "realm_order_min" in require:
        if curriculum.realm_order(player.realm_key) < int(require["realm_order_min"]):
            return False
    if "affinity_min" in require:
        if player.npc_affinity_for(npc_id) < int(require["affinity_min"]):
            return False
    if "task_done" in require:
        task_id = require["task_done"]
        completed = player.completed_tasks + player.debug_completed + player.branch_completed
        if task_id not in completed:
            return False
    return True


def _visible_options(player, npc_id: str, options: list[dict]) -> list[dict]:
    return [option for option in options if _require_met(player, npc_id, option.get("require"))]


def _npc_context(player, npc_id: str) -> dict:
    return npcs_mod.for_player(player, npc_id) or {"id": npc_id, "affinity": 0, "relationship_name": "陌生"}


def _apply_reward(player, action: dict) -> str:
    parts = []
    if action.get("cultivation"):
        player.add_cultivation(int(action["cultivation"]))
        parts.append("修为 +%d" % int(action["cultivation"]))
    if action.get("comprehension"):
        player.add_comprehension(int(action["comprehension"]))
        parts.append("悟性 +%d" % int(action["comprehension"]))
    if action.get("mindset"):
        player.add_mindset(int(action["mindset"]))
        parts.append("心境 %+d" % int(action["mindset"]))
    if action.get("debug_exp"):
        player.add_debug_exp(int(action["debug_exp"]))
        parts.append("Debug 经验 +%d" % int(action["debug_exp"]))
    item_id = action.get("item")
    if item_id:
        player.add_item(item_id)
        name = (items_mod.get_item(item_id) or {}).get("name", item_id)
        parts.append("获得「%s」" % name)
    ach = action.get("achievement")
    if ach and player.unlock_achievement(ach):
        parts.append("解锁成就「%s」" % ach)
    return "；".join(parts) if parts else ""


def apply_actions(player, actions: list[dict], npc_id: str = "") -> list[str]:
    """执行节点动作（每个 action id 对玩家只生效一次），返回效果描述列表。"""
    effects = []
    for action in actions or []:
        action_id = action.get("id") or ""
        kind = action.get("type", "")
        if not action_id:
            continue
        if player.has_npc_action("__dialogue__", action_id):
            continue
        msg = ""
        if kind == "reward":
            msg = _apply_reward(player, action)
        elif kind == "unlock_task":
            task_id = action.get("task_id", "")
            if task_id and task_id not in player.branch_unlocked:
                player.branch_unlocked.append(task_id)
                msg = "获得新机缘（支线任务）"
        elif kind == "unlock_secret":
            secret_id = action.get("secret_id", "")
            if secret_id and secret_id not in player.secret_unlocked:
                player.secret_unlocked.append(secret_id)
                msg = "秘境入口已标记于罗盘"
        elif kind == "learn_technique":
            tech = action.get("technique_id", "")
            if tech:
                player.learn_technique(tech)
                msg = "习得功法"
        elif kind == "affinity":
            target_npc = action.get("npc_id") or npc_id
            value = int(action.get("value", 0))
            if target_npc and value:
                player.add_npc_affinity(target_npc, value)
                npc_name = (npcs_mod.get_npc(target_npc) or {}).get("name", target_npc)
                msg = "%s好感%+d" % (npc_name, value)
        elif kind == "flag":
            msg = ""
        if msg:
            effects.append(msg)
        player.mark_npc_action("__dialogue__", action_id)
    return effects


def enter(player, npc_id: str) -> dict:
    """进入对话：返回起始节点。"""
    node_id = start_node_id(npc_id)
    node = get_node(npc_id, node_id) or {}
    npc_state = _npc_context(player, npc_id)
    return {
        "npc_id": npc_id,
        "node_id": node_id,
        "text": node.get("text", ""),
        "options": _visible_options(player, npc_id, node.get("options", [])),
        "effects": [],
        "npc": npc_state,
        "affinity": npc_state["affinity"],
        "relationship": npc_state["relationship_name"],
    }


def choose(player, npc_id: str, node_id: str, option_index: int) -> dict:
    """选择选项：推进到目标节点并执行其动作。返回新节点与效果。"""
    node = get_node(npc_id, node_id) or {}
    options = _visible_options(player, npc_id, node.get("options", []))
    if option_index < 0 or option_index >= len(options):
        raise ValueError("无效的对话选项。")
    target = options[option_index].get("goto", END_NODE)
    if target == END_NODE:
        npc_state = _npc_context(player, npc_id)
        return {"npc_id": npc_id, "node_id": END_NODE, "text": "", "options": [], "effects": [], "ended": True, "npc": npc_state, "affinity": npc_state["affinity"], "relationship": npc_state["relationship_name"]}
    target_node = get_node(npc_id, target) or {}
    if not _require_met(player, npc_id, target_node.get("require")):
        raise ValueError("当前关系尚未解锁这段对话。")
    actions = list(target_node.get("actions", []))
    if target_node.get("affinity"):
        actions.append({"id": "affinity:%s:%s" % (npc_id, target), "type": "affinity", "value": target_node["affinity"]})
    effects = apply_actions(player, actions, npc_id)
    npc_state = _npc_context(player, npc_id)
    return {
        "npc_id": npc_id,
        "node_id": target,
        "text": target_node.get("text", ""),
        "options": _visible_options(player, npc_id, target_node.get("options", [])),
        "effects": effects,
        "ended": False,
        "npc": npc_state,
        "affinity": npc_state["affinity"],
        "relationship": npc_state["relationship_name"],
    }
