# -*- coding: utf-8 -*-
"""存档系统：玩家进度以 JSON 文件形式保存在 saves/ 目录（多槽位）。"""

from __future__ import annotations

import json
import os

from . import config
from .player import Player


def _slot_path(slot: str | None = None) -> str:
    slot = slot or config.DEFAULT_SLOT
    # 槽位名仅允许安全字符，避免路径穿越
    safe = "".join(c for c in slot if c.isalnum() or c in "_-.").strip(".")
    safe = safe or "default"
    return os.path.join(config.SAVE_DIR, safe + ".json")


def save_exists(slot: str | None = None) -> bool:
    return os.path.exists(_slot_path(slot))


def save_game(player: Player, slot: str | None = None) -> str:
    """保存玩家进度，返回保存时间。"""
    os.makedirs(config.SAVE_DIR, exist_ok=True)
    player.touch()
    path = _slot_path(slot)
    data = {
        "version": 2,
        "player": player.to_dict(),
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return player.updated_at


def load_game(slot: str | None = None) -> Player | None:
    """读取存档（自动兼容 V0.1 的 version 1 存档）；文件不存在或损坏时返回 None。"""
    path = _slot_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return Player.from_dict(data["player"])
    except Exception:
        return None


def delete_save(slot: str | None = None) -> bool:
    """删除指定槽位存档，返回是否删除成功。"""
    path = _slot_path(slot)
    if not os.path.exists(path):
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def list_saves() -> list[dict]:
    """列出所有存档（槽位、修改时间、角色信息）。"""
    if not os.path.isdir(config.SAVE_DIR):
        return []
    result = []
    for name in sorted(os.listdir(config.SAVE_DIR)):
        if name.endswith(".json") and not name.endswith(".tmp.json"):
            path = os.path.join(config.SAVE_DIR, name)
            try:
                mtime = os.path.getmtime(path)
                player = load_game(name[:-5])
                result.append({
                    "slot": name[:-5],
                    "path": path,
                    "mtime": mtime,
                    "size": os.path.getsize(path),
                    "player": player.to_dict() if player else None,
                })
            except OSError:
                continue
    return result
