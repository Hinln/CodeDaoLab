# -*- coding: utf-8 -*-
"""课程数据加载与查询。

加载 game/data 下的 curriculum.json 与 tasks.json（均为 UTF-8 编码，
允许带 BOM），提供境界、任务、炼丹房、天劫等数据的统一访问入口。

打包（zipapp）运行时数据文件位于归档内部，因此统一通过
importlib.resources 读取；源码运行时同样适用。
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_json(name: str) -> dict:
    """从归档（zipapp）或磁盘读取课程 JSON。"""
    try:
        text = resources.files("game.data").joinpath(name).read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        # 回退：源码目录直接读文件
        with open(os.path.join(_DATA_DIR, name), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def curriculum() -> dict:
    """返回完整课程数据（境界 + 炼丹房解锁 + 天劫定义）。"""
    return _load_json("curriculum.json")


@lru_cache(maxsize=1)
def tasks() -> dict:
    """返回全部任务定义。"""
    return _load_json("tasks.json")


def all_tasks() -> dict:
    return tasks()["tasks"]


def get_task(task_id: str) -> dict | None:
    return tasks()["tasks"].get(task_id)


def realms() -> list[dict]:
    return curriculum()["realms"]


def realm_by_key(key: str) -> dict | None:
    for realm in realms():
        if realm["key"] == key:
            return realm
    return None


def realm_order(key: str) -> int:
    realm = realm_by_key(key)
    return realm["order"] if realm else -1


def next_realm_key(key: str) -> str | None:
    order = realm_order(key)
    for realm in realms():
        if realm["order"] == order + 1:
            return realm["key"]
    return None


def realm_tasks(key: str) -> list[str]:
    realm = realm_by_key(key)
    return list(realm["tasks"]) if realm else []


def debug_unlock_map() -> dict:
    return curriculum()["debug_unlock"]


def tribulation() -> dict:
    return curriculum()["tribulation"]


def tribulation_waves() -> dict:
    return tasks()["tribulation_waves"]


def major_realms() -> list[dict]:
    """大境界链（凡人/炼气/筑基/金丹/…/渡劫）。"""
    return curriculum().get("major_realms", [])


def major_realm_for(realm_key: str) -> dict:
    """返回某小境界所属的大境界（含未来预留空阶段）。"""
    for major in major_realms():
        if realm_key in major.get("stages", []):
            return major
    # 未知境界：返回自身作为兜底
    return {"key": realm_key, "name": realm_key, "stages": []}


def major_realm_order(realm_key: str) -> int:
    for i, major in enumerate(major_realms()):
        if realm_key in major.get("stages", []):
            return i
    return -1
