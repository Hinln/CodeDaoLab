# -*- coding: utf-8 -*-
"""玩家状态模型（V0.2 扩展）。

在 V0.1 基础上新增：
- 属性：悟性 comprehension、心境 mindset、Debug 经验 debug_exp
- 成就 achievements、道具 items、已学功法 techniques
- NPC 对话状态 npc_flags、秘境历练记录 secret_log
所有新增字段均有默认值，兼容旧存档（缺字段时自动补默认）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class Player:
    """玩家档案：记录境界、属性、任务进度、成就与各类游戏状态。"""

    name: str = "无名散修"
    spirit_root: str = "金"          # 灵根（金/木/水/火/土，影响初始属性）
    realm_key: str = "mortal"        # 当前境界（大境界.小境界，见 curriculum）
    completed_tasks: list[str] = field(default_factory=list)   # 主线任务
    debug_completed: list[str] = field(default_factory=list)   # 炼丹房任务
    branch_completed: list[str] = field(default_factory=list)  # 支线任务
    branch_unlocked: list[str] = field(default_factory=list)   # 已解锁（NPC 对话触发）的支线
    secret_unlocked: list[str] = field(default_factory=list)   # 已解锁的秘境
    tribulation_passed: list[str] = field(default_factory=list)  # 已渡天劫波次
    cultivation: int = 0             # 修为（经验）
    comprehension: int = 10          # 悟性：影响 AI 师尊提示分级节奏
    mindset: int = 100               # 心境：连续失败会下降，影响引导语气
    debug_exp: int = 0               # Debug 经验
    pending_breakthrough: bool = False  # 当前境界任务完成，等待突破
    founded: bool = False            # 是否已筑基（历史字段，V0.2 由境界链取代）
    achievements: list[str] = field(default_factory=list)   # 已获得成就 id
    attempts: dict[str, int] = field(default_factory=dict)   # 各任务提交失败次数 {task_id: n}
    streak: int = 0                 # 连续通过验证次数
    title: str = ""                 # 称号（由成就授予）
    items: dict[str, int] = field(default_factory=dict)     # 道具背包 {item_id: count}
    techniques: list[str] = field(default_factory=list)     # 已学功法（藏经阁）
    npc_flags: dict[str, list[str]] = field(default_factory=dict)  # NPC 已触发动作
    secret_log: dict[str, int] = field(default_factory=dict)       # 秘境通关次数 {realm_id: count}
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def touch(self) -> None:
        self.updated_at = _now_iso()

    # ---------- 属性操作 ----------

    def add_cultivation(self, value: int) -> None:
        self.cultivation += max(0, int(value))

    def add_comprehension(self, value: int) -> None:
        self.comprehension += int(value)

    def add_mindset(self, value: int) -> None:
        """心境变化，钳制在 [0, 200]。"""
        self.mindset = max(0, min(200, self.mindset + int(value)))

    def add_debug_exp(self, value: int) -> None:
        self.debug_exp += max(0, int(value))

    def add_item(self, item_id: str, count: int = 1) -> None:
        self.items[item_id] = self.items.get(item_id, 0) + count

    def consume_item(self, item_id: str, count: int = 1) -> bool:
        cur = self.items.get(item_id, 0)
        if cur < count:
            return False
        if cur == count:
            self.items.pop(item_id, None)
        else:
            self.items[item_id] = cur - count
        return True

    def has_item(self, item_id: str, count: int = 1) -> bool:
        return self.items.get(item_id, 0) >= count

    def record_success(self) -> None:
        self.streak += 1
        self.add_mindset(2)

    def reset_streak(self) -> None:
        self.streak = 0

    def record_failure(self, task_id: str) -> None:
        self.attempts[task_id] = self.attempts.get(task_id, 0) + 1

    def clear_attempts(self, task_id: str) -> None:
        self.attempts.pop(task_id, None)

    def attempt_count(self, task_id: str) -> int:
        return self.attempts.get(task_id, 0)

    def learn_technique(self, technique_id: str) -> None:
        if technique_id not in self.techniques:
            self.techniques.append(technique_id)

    def unlock_achievement(self, achievement_id: str) -> bool:
        """返回是否为新解锁。"""
        if achievement_id in self.achievements:
            return False
        self.achievements.append(achievement_id)
        return True

    def mark_npc_action(self, npc_id: str, action_id: str) -> None:
        flags = self.npc_flags.setdefault(npc_id, [])
        if action_id not in flags:
            flags.append(action_id)

    def has_npc_action(self, npc_id: str, action_id: str) -> bool:
        return action_id in self.npc_flags.get(npc_id, [])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "spirit_root": self.spirit_root,
            "realm_key": self.realm_key,
            "completed_tasks": list(self.completed_tasks),
            "debug_completed": list(self.debug_completed),
            "branch_completed": list(self.branch_completed),
            "branch_unlocked": list(self.branch_unlocked),
            "secret_unlocked": list(self.secret_unlocked),
            "tribulation_passed": list(self.tribulation_passed),
            "cultivation": self.cultivation,
            "comprehension": self.comprehension,
            "mindset": self.mindset,
            "debug_exp": self.debug_exp,
            "pending_breakthrough": self.pending_breakthrough,
            "founded": self.founded,
            "achievements": list(self.achievements),
            "attempts": dict(self.attempts),
            "streak": self.streak,
            "title": self.title,
            "items": dict(self.items),
            "techniques": list(self.techniques),
            "npc_flags": {k: list(v) for k, v in self.npc_flags.items()},
            "secret_log": dict(self.secret_log),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(
            name=data.get("name", "无名散修"),
            spirit_root=data.get("spirit_root", "金"),
            realm_key=data.get("realm_key", "mortal"),
            completed_tasks=list(data.get("completed_tasks", [])),
            debug_completed=list(data.get("debug_completed", [])),
            branch_completed=list(data.get("branch_completed", [])),
            branch_unlocked=list(data.get("branch_unlocked", [])),
            secret_unlocked=list(data.get("secret_unlocked", [])),
            tribulation_passed=list(data.get("tribulation_passed", [])),
            cultivation=int(data.get("cultivation", 0)),
            comprehension=int(data.get("comprehension", 10)),
            mindset=int(data.get("mindset", 100)),
            debug_exp=int(data.get("debug_exp", 0)),
            pending_breakthrough=bool(data.get("pending_breakthrough", False)),
            founded=bool(data.get("founded", False)),
            achievements=list(data.get("achievements", [])),
            attempts={str(k): int(v) for k, v in data.get("attempts", {}).items()},
            streak=int(data.get("streak", 0)),
            title=data.get("title", ""),
            items=dict(data.get("items", {})),
            techniques=list(data.get("techniques", [])),
            npc_flags={k: list(v) for k, v in data.get("npc_flags", {}).items()},
            secret_log=dict(data.get("secret_log", {})),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
