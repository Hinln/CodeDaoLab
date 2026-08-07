# -*- coding: utf-8 -*-
"""功法系统（藏经阁）：Python 知识体系 = 功法。

功法由课程数据（curriculum.json 各境界的教学块）派生：
- 功法 id = 境界 key；
- 玩家突破进入某境界时自动习得该境界功法；
- 藏经阁可回顾已学功法（教学内容）。
"""

from __future__ import annotations

from . import curriculum


def technique_for_realm(realm: dict) -> dict | None:
    """由境界数据构造功法；无教学内容的境界不构成功法。"""
    teaching = realm.get("teaching") or []
    if not teaching:
        return None
    title = teaching[0].get("title", realm["name"])
    return {
        "id": realm["key"],
        "realm_key": realm["key"],
        "name": realm["name"],
        "title": title,
        "intro": realm.get("intro", ""),
        "teaching": teaching,
    }


def all_techniques() -> list[dict]:
    result = []
    for realm in curriculum.realms():
        tech = technique_for_realm(realm)
        if tech:
            result.append(tech)
    return result


def get_technique(technique_id: str) -> dict | None:
    for tech in all_techniques():
        if tech["id"] == technique_id:
            return tech
    return None


def learn_realm_technique(player, realm_key: str) -> bool:
    """玩家习得某境界功法；成功返回 True。"""
    realm = curriculum.realm_by_key(realm_key)
    if not realm:
        return False
    tech = technique_for_realm(realm)
    if not tech:
        return False
    player.learn_technique(tech["id"])
    return True
