# -*- coding: utf-8 -*-
"""任务系统：真实执行验证 + 游戏进度推进。

验证原则：绝不做关键词匹配，全部通过真实执行玩家代码并比对
输出 / 函数用例结果来判定。
"""

from __future__ import annotations

import json

from . import curriculum
from . import sandbox
from .player import Player

# 函数验证片段（在沙箱内与玩家代码同命名空间执行）
FUNC_HARNESS = '''
import json as _json
_cases = _json.loads(__CA_CASES__)
_method = __CA_METHOD__
_results = []
_fn = globals().get(__CA_FUNC__)
if _fn is None:
    _results.append({"pass": False, "reason": "未找到函数「" + __CA_FUNC__ + "」，请检查函数名是否拼写正确。"})
else:
    for _c in _cases:
        try:
            _init_args = _c.get("init_args", [])
            _init_kwargs = _c.get("init_kwargs", {})
            if _method:
                _obj = _fn(*_init_args, **_init_kwargs)
            _expected_raise = _c.get("raises")
            if _expected_raise:
                try:
                    if _method:
                        _actual = getattr(_obj, _method)(*_c.get("args", []), **_c.get("kwargs", {}))
                    else:
                        _actual = _fn(*_c.get("args", []), **_c.get("kwargs", {}))
                    _results.append({"pass": False, "expected": "raise " + str(_expected_raise), "actual": "未抛出异常"})
                except Exception as _e:
                    _ok = type(_e).__name__ == _expected_raise
                    _results.append({"pass": _ok, "expected": "raise " + str(_expected_raise), "actual": type(_e).__name__})
                continue
            if _method:
                _actual = getattr(_obj, _method)(*_c.get("args", []), **_c.get("kwargs", {}))
            else:
                _actual = _fn(*_c.get("args", []), **_c.get("kwargs", {}))
            _expected = _c.get("expected")
            _ok = _actual == _expected
            if not _ok and isinstance(_expected, float) and isinstance(_actual, (int, float)):
                _ok = abs(_actual - _expected) < 1e-9
            _results.append({"pass": _ok, "expected": repr(_expected), "actual": repr(_actual)})
        except Exception as _e:
            _results.append({"pass": False, "error": str(_e)})
print(_json.dumps(_results, ensure_ascii=False))
'''

MAIN = "main"
DEBUG = "debug"
WAVE = "wave"
BRANCH = "branch"
TRIAL = "trial"
SECRET = "secret"


def normalize_output(text: str) -> str:
    """规范化输出用于精确比对：统一换行、去除行尾空白与多余空行。"""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


class ValidationOutcome:
    """一次提交验证的结果。"""

    def __init__(self, passed: bool, run: sandbox.RunResult, details=None, message: str = ""):
        self.passed = passed
        self.run = run
        self.details = details or []
        self.message = message or self._default_message()

    def _default_message(self) -> str:
        if self.run.status == "ok":
            if self.passed:
                return "功法运转如意，大道可期！"
            return "灵力尚有不谐之处，请继续参悟。"
        return self.run.message

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "message": self.message,
            "run": self.run.to_dict(),
            "details": self.details,
        }


def validate_task(task: dict, code: str) -> ValidationOutcome:
    """对玩家提交的代码做真实执行验证。"""
    check = task.get("check", {})
    mode = check.get("mode", "output")
    time_limit = float(task.get("time_limit", 5))
    inputs = list(check.get("inputs", []))

    if mode == "function":
        cases_json = json.dumps(check.get("cases", []), ensure_ascii=False)
        r = sandbox.run_validation(
            code,
            cases_json,
            FUNC_HARNESS,
            inputs=inputs,
            time_limit=time_limit,
            func_name=check.get("func_name"),
            method=check.get("method"),
            seed_files=check.get("seed_files"),
        )
        if r.status != "ok":
            return ValidationOutcome(False, r)
        try:
            details = json.loads(r.epilogue_output or "[]")
        except Exception:
            details = [{"pass": False, "error": "验证结果无法解析"}]
        passed = bool(details) and all(d.get("pass") for d in details)
        return ValidationOutcome(passed, r, details=details)

    # output 模式
    r = sandbox.run_player_code(code, inputs=inputs, time_limit=time_limit, seed_files=check.get("seed_files"))
    if r.status != "ok":
        return ValidationOutcome(False, r)
    actual = normalize_output(r.stdout)
    expected_cfg = check.get("expected", {})
    if "exact" in expected_cfg:
        expected = normalize_output(expected_cfg["exact"])
        passed = actual == expected
    else:
        contains = expected_cfg.get("contains", [])
        passed = bool(contains) and all(c in actual for c in contains)
    if not passed and "exact" in expected_cfg:
        details = [{
            "pass": False,
            "expected": repr(expected_cfg["exact"]),
            "actual": repr(r.stdout),
            "hint": "输出与预期不符，请检查每一条 print 的内容与顺序。",
        }]
    else:
        details = []
    return ValidationOutcome(passed, r, details=details)


# ---------- 进度推进 ----------

def current_task_id(player: Player) -> str | None:
    """当前主线任务：本境界中第一个未完成的任务；全完成则返回 None。"""
    for task_id in curriculum.realm_tasks(player.realm_key):
        if task_id not in player.completed_tasks:
            return task_id
    return None


def is_realm_complete(player: Player, realm_key: str) -> bool:
    return all(t in player.completed_tasks for t in curriculum.realm_tasks(realm_key))


def unlocked_debug_tasks(player: Player) -> list[str]:
    """按境界解锁的炼丹房任务（已完成的不再列出）。"""
    result = []
    unlock_map = curriculum.debug_unlock_map()
    player_order = curriculum.realm_order(player.realm_key)
    for task_id in curriculum.tasks()["debug_tasks"]:
        need = unlock_map.get(task_id)
        if task_id in player.debug_completed:
            continue
        if need and curriculum.realm_order(need) <= player_order:
            result.append(task_id)
    return result


def realm_requirement_met(player: Player, task: dict) -> bool:
    """任务的前置境界要求：requires_realm 为境界 key（含该境界）。"""
    need = task.get("requires_realm")
    if not need:
        return True
    need_order = curriculum.realm_order(need)
    player_order = curriculum.realm_order(player.realm_key)
    return need_order >= 0 and player_order >= need_order


def unlocked_branch_tasks(player: Player) -> list[str]:
    """已解锁且境界达标的支线任务（按数据定义顺序）。"""
    result = []
    for task_id in player.branch_unlocked:
        task = curriculum.get_task(task_id)
        if not task or task.get("kind") != BRANCH:
            continue
        if task_id in player.branch_completed:
            continue
        if not realm_requirement_met(player, task):
            continue
        result.append(task_id)
    return result


def apply_rewards(player: Player, task: dict) -> dict:
    """应用任务奖励（修为/悟性/Debug 经验/道具），返回奖励明细。"""
    rewards = task.get("rewards") or {}
    details = {}
    cultivation = int(task.get("reward", 0) or rewards.get("cultivation", 0))
    if cultivation:
        player.add_cultivation(cultivation)
        details["cultivation"] = cultivation
    if rewards.get("comprehension"):
        player.add_comprehension(int(rewards["comprehension"]))
        details["comprehension"] = int(rewards["comprehension"])
    if rewards.get("debug_exp"):
        player.add_debug_exp(int(rewards["debug_exp"]))
        details["debug_exp"] = int(rewards["debug_exp"])
    if rewards.get("mindset"):
        player.add_mindset(int(rewards["mindset"]))
        details["mindset"] = int(rewards["mindset"])
    for item_id in rewards.get("items", []):
        player.add_item(item_id)
        details.setdefault("items", []).append(item_id)
    from . import techniques
    technique_gain = techniques.award_task_progress(player)
    if technique_gain:
        details["technique_progress"] = technique_gain
    return details


def complete_branch_task(player: Player, task: dict) -> dict:
    """完成支线任务：记录、发放奖励。"""
    task_id = task["id"]
    player.branch_completed.append(task_id)
    rewards = apply_rewards(player, task)
    return {"task_completed": task_id, "rewards": rewards}


def is_tribulation_unlocked(player: Player) -> bool:
    """炼气大圆满全部任务完成（或已筑基）后，渡劫台开启。"""
    if player.founded:
        return True
    return is_realm_complete(player, "qi10")


def current_wave_key(player: Player) -> str | None:
    """当前应渡的天劫波次；全部渡过返回 None。"""
    if not is_tribulation_unlocked(player):
        return None
    for wave in sorted(curriculum.tribulation_waves().values(), key=lambda w: w["order"]):
        task_id = wave["task"]
        if task_id not in player.tribulation_passed:
            return wave["key"]
    return None


def task_visible_kind(player: Player, task: dict) -> str | None:
    """判断某任务当前对玩家是否可见/可做，返回任务类别。"""
    kind = task.get("kind", MAIN)
    if kind == MAIN:
        if task["id"] == current_task_id(player) and task["realm"] == player.realm_key:
            return MAIN
        return None
    if kind == DEBUG:
        if task["id"] in unlocked_debug_tasks(player):
            return DEBUG
        return None
    if kind == BRANCH:
        if task["id"] in unlocked_branch_tasks(player):
            return BRANCH
        return None
    if kind == TRIAL:
        if tasks_trial_available(player, task):
            return TRIAL
        return None
    if kind == WAVE:
        wave = curriculum.tribulation_waves().get(task.get("wave_key", ""))
        if not wave:
            return None
        if wave["key"] == current_wave_key(player):
            return WAVE
        return None
    return None


def tasks_trial_available(player: Player, task: dict) -> bool:
    """综合试炼任务是否可见：属于当前境界且为当前进行中的任务时可见。"""
    if task.get("kind") != TRIAL:
        return False
    if task["id"] not in curriculum.realm_tasks(player.realm_key):
        return False
    return task["id"] == current_task_id(player)


def complete_main_task(player: Player, task: dict) -> dict:
    """完成主线任务：记录、加修为、判定突破资格。"""
    task_id = task["id"]
    player.completed_tasks.append(task_id)
    rewards = apply_rewards(player, task)
    events = {"task_completed": task_id, "realm_complete": False, "tribulation_unlocked": False, "rewards": rewards}
    if is_realm_complete(player, player.realm_key):
        player.pending_breakthrough = True
        events["realm_complete"] = True
        if player.realm_key == "qi10":
            events["tribulation_unlocked"] = True
    return events


def complete_debug_task(player: Player, task: dict) -> dict:
    player.debug_completed.append(task["id"])
    player.add_debug_exp(int(task.get("reward", 0)))
    rewards = apply_rewards(player, task)
    return {"task_completed": task["id"], "rewards": rewards}


def complete_wave(player: Player, task: dict) -> dict:
    player.tribulation_passed.append(task["id"])
    rewards = apply_rewards(player, task)
    return {"wave_completed": task["wave_key"], "rewards": rewards}


def breakthrough(player: Player) -> dict:
    """执行境界突破。返回事件信息；不满足条件时抛出 ValueError。"""
    if not player.pending_breakthrough:
        raise ValueError("当前境界尚未圆满，无法突破。")
    if player.realm_key == "qi10":
        if current_wave_key(player) is not None:
            raise ValueError("筑基天劫尚未渡尽，先去渡劫台吧。")
        player.realm_key = "foundation"
        player.founded = True
        player.pending_breakthrough = False
        from . import techniques
        techniques.learn_realm_technique(player, "foundation")
        return {"type": "tribulation", "from": "qi10", "to": "foundation", "founded": True}
    nxt = curriculum.next_realm_key(player.realm_key)
    if not nxt:
        raise ValueError("已至尽头，无需突破。")
    old = player.realm_key
    player.realm_key = nxt
    player.pending_breakthrough = False
    from . import techniques
    techniques.learn_realm_technique(player, nxt)
    return {"type": "breakthrough", "from": old, "to": nxt, "founded": False}
