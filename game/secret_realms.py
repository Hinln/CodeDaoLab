# -*- coding: utf-8 -*-
"""秘境系统：数据驱动挑战模板 + 参数随机化 + 真实沙箱验证。

- 每个秘境（secret_realms.json）定义境界门槛、奖励与模板池；
- 进入秘境时从模板池随机选取模板并随机化参数，生成全新挑战；
- 生成结果必须在沙箱中真实运行参考答案自检（不通过则重新生成），
  保证随机任务「可解且可验证」；
- 通关奖励走 tasks.apply_rewards（修为/悟性/道具），记录 secret_log。
"""

from __future__ import annotations

import json
import os
import random
from functools import lru_cache
from importlib import resources

from . import curriculum, tasks

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load() -> dict:
    try:
        text = resources.files("game.data").joinpath("secret_realms.json").read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception:
        with open(os.path.join(_DATA_DIR, "secret_realms.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)


@lru_cache(maxsize=1)
def secret_realms() -> dict:
    return _load()["secret_realms"]


def get_realm(realm_id: str) -> dict | None:
    return secret_realms().get(realm_id)


# ---------- 模板生成器：参数随机化 + 产出标准 check/solution ----------

def _gen_sum_3_multiples(rng):
    n = rng.randint(10, 30)
    count = sum(1 for i in range(1, n + 1) if i % 3 == 0)
    total = sum(i for i in range(1, n + 1) if i % 3 == 0)
    return {
        "title": "灵石阵法",
        "story": "青云秘境云雾缭绕，眼前浮现一座由 1 至 " + str(n) + " 组成的灵石阵法。"
                 "阵眼要求：统计 1 到 " + str(n) + " 中『3 的倍数』的灵石数量，并累加它们的灵力总和。先报数量，再报总和。",
        "hints": ["用 range(1, n + 1) 遍历", "if i % 3 == 0 判断是否为 3 的倍数", "分别用变量统计数量与总和"],
        "starter_code": "total = 0\ncount = 0\nfor i in range(1, " + str(n) + " + 1):\n    # 补全\n    pass\nprint(count)\nprint(total)",
        "check": {"mode": "output", "expected": {"exact": str(count) + "\n" + str(total)}},
        "solution": "count = 0\ntotal = 0\nfor i in range(1, " + str(n) + " + 1):\n    if i % 3 == 0:\n        count += 1\n        total += i\nprint(count)\nprint(total)",
    }


def _gen_word_transform(rng):
    word = rng.choice(["qingyun", "wanxiang", "tiangong", "lingmai", "yunjian", "danlu"])
    expected = word.upper() + " " + str(len(word))
    return {
        "title": "云篆显形",
        "story": "云墙上浮现一行真言「" + word + "」。请施展净字诀：将真言转为全大写，并在其后报出真言的长度（字符数），以空格分隔。",
        "hints": ["word.upper() 转大写", "len(word) 得长度", "print(word.upper(), len(word)) 以空格分隔输出"],
        "starter_code": "w = \"" + word + "\"\n# 输出：大写形式 空格 长度",
        "check": {"mode": "output", "expected": {"exact": expected}},
        "solution": "w = \"" + word + "\"\nprint(w.upper(), len(w))",
    }


def _gen_list_stats(rng):
    lst = [rng.randint(-20, 50) for _ in range(5)]
    expected = "\n".join(str(v) for v in (min(lst), max(lst), sum(lst)))
    return {
        "title": "灵材清点",
        "story": "秘境药圃中散落着 5 份灵材，灵性值依次为：" + str(lst) + "。请按序报出：最小值、最大值、总和（各占一行）。",
        "hints": ["min(lst) 取最小值", "max(lst) 取最大值", "sum(lst) 取总和"],
        "starter_code": "lst = " + str(lst) + "\n# 依次输出最小值、最大值、总和",
        "check": {"mode": "output", "expected": {"exact": expected}},
        "solution": "lst = " + str(lst) + "\nprint(min(lst))\nprint(max(lst))\nprint(sum(lst))",
    }


def _gen_function_multiply(rng):
    a, b = rng.randint(2, 9), rng.randint(3, 12)
    expected = a * b
    return {
        "title": "翻倍诀",
        "story": "秘境守将要求：写功法 calc(a, b)，返回 a 与 b 相乘之积。试炼用例包含 " + str(a) + " × " + str(b) + "。",
        "hints": ["def calc(a, b):", "return a * b"],
        "starter_code": "def calc(a, b):\n    # 补全\n    pass",
        "check": {
            "mode": "function",
            "func_name": "calc",
            "cases": [
                {"args": [a, b], "expected": expected},
                {"args": [b, a], "expected": expected},
                {"args": [1, 7], "expected": 7},
            ],
        },
        "solution": "def calc(a, b):\n    return a * b",
    }


def _gen_safe_divide_v2(rng):
    a, b = rng.randint(10, 99), rng.randint(2, 9)
    q = a / b
    return {
        "title": "万象不灭",
        "story": "幻境中妖风阵阵，除数可能为 0。写功法 safe_divide(a, b)：正常时返回 a 除以 b 的商；若 b 为 0 则返回「不可除零」，绝不让功法崩溃。",
        "hints": ["用 try/except 包裹除法", "except ZeroDivisionError 分支返回「不可除零」"],
        "starter_code": "def safe_divide(a, b):\n    # 补全\n    pass",
        "check": {
            "mode": "function",
            "func_name": "safe_divide",
            "cases": [
                {"args": [a, b], "expected": q},
                {"args": [a, 0], "expected": "不可除零"},
                {"args": [36, 6], "expected": 6.0},
            ],
        },
        "solution": "def safe_divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return \"不可除零\"",
    }


def _gen_string_clean(rng):
    phrase = rng.choice(["code ascension", "python dao", "cloud realm", "spirit script"])
    cleaned = phrase.strip().title().replace(" ", "_")
    return {
        "title": "万象净字",
        "story": "幻境石碑刻着「  " + phrase + "  」（首尾带空格）。请去除首尾空白、令英文单词首字母大写，并把空格替换为下划线，报出净化后的真言。",
        "hints": ["strip() 去首尾空白", "title() 首字母大写", "replace(\" \", \"_\") 替换空格"],
        "starter_code": "s = \"  " + phrase + "  \"\n# 输出净化后的真言",
        "check": {"mode": "output", "expected": {"exact": cleaned}},
        "solution": "s = \"  " + phrase + "  \"\nprint(s.strip().title().replace(\" \", \"_\"))",
    }


def _gen_count_chars(rng):
    text = rng.choice(["qingyun wanxiang tiangong", "python code ascension", "dao heart tribulation"])
    ch = rng.choice("aeiou")
    count = text.count(ch)
    return {
        "title": "观文数珠",
        "story": "幻境经文为「" + text + "」。请数出其中字符 '" + ch + "' 出现的次数并报出。",
        "hints": ["text.count(字符) 统计出现次数", "用引号包裹要统计的字符"],
        "starter_code": "text = \"" + text + "\"\n# 输出字符 " + ch + " 的出现次数",
        "check": {"mode": "output", "expected": {"exact": str(count)}},
        "solution": "text = \"" + text + "\"\nprint(text.count(\"" + ch + "\"))",
    }


def _gen_class_cultivate(rng):
    name = rng.choice(["青锋剑灵", "紫电剑灵", "赤霄剑灵"])
    level = rng.randint(1, 5)
    n = rng.randint(2, 5)
    expected = level + n
    return {
        "title": "天宫点灵",
        "story": "代码天宫之上，需点化剑灵「" + name + "」。定义类 Ling：以 name 与 level 初始化；方法 cultivate(n) 将境界提升 n 层并返回新境界。随后施展 Ling(\"" + name + "\", " + str(level) + ").cultivate(" + str(n) + ") 并报出结果。",
        "hints": ["__init__ 记录 self.name 与 self.level", "cultivate 中 self.level += n 并 return self.level", "实例化后调用 cultivate 并 print"],
        "starter_code": "class Ling:\n    def __init__(self, name, level):\n        # 补全\n        pass\n\n    def cultivate(self, n):\n        # 补全\n        pass\n\nprint(Ling(\"" + name + "\", " + str(level) + ").cultivate(" + str(n) + "))",
        "check": {"mode": "output", "expected": {"exact": str(expected)}},
        "solution": "class Ling:\n    def __init__(self, name, level):\n        self.name = name\n        self.level = level\n\n    def cultivate(self, n):\n        self.level += n\n        return self.level\n\nprint(Ling(\"" + name + "\", " + str(level) + ").cultivate(" + str(n) + "))",
    }


def _gen_module_summon(rng):
    mod_name = rng.choice(["spells", "arts"])
    base = rng.randint(3, 7)
    x = rng.randint(2, 9)
    expected = x * base
    return {
        "title": "天宫藏经",
        "story": "天宫藏经阁要求你写下秘籍 " + mod_name + ".py——内含功法 boost(x)，返回 x 的 " + str(base) + " 倍；随后引入并施展 boost(" + str(x) + ")，报出结果。",
        "hints": ["用 open 写入秘籍（注意 \\n 与缩进）", "秘籍内定义 def boost(x): return x * " + str(base), "import " + mod_name + " 后调用"],
        "starter_code": "# 写下秘籍 " + mod_name + ".py\nwith open(\"" + mod_name + ".py\", \"w\", encoding=\"utf-8\") as f:\n    f.write(\"\")  # 请写入功法\n\nimport " + mod_name + "\nprint(" + mod_name + ".boost(" + str(x) + "))",
        "check": {"mode": "output", "expected": {"exact": str(expected)}},
        "solution": "with open(\"" + mod_name + ".py\", \"w\", encoding=\"utf-8\") as f:\n    f.write(\"def boost(x):\\n    return x * " + str(base) + "\\n\")\n\nimport " + mod_name + "\nprint(" + mod_name + ".boost(" + str(x) + "))",
    }


_GENERATORS = {
    "sum_3_multiples": _gen_sum_3_multiples,
    "word_transform": _gen_word_transform,
    "list_stats": _gen_list_stats,
    "function_multiply": _gen_function_multiply,
    "safe_divide_v2": _gen_safe_divide_v2,
    "string_clean": _gen_string_clean,
    "count_chars": _gen_count_chars,
    "class_cultivate": _gen_class_cultivate,
    "module_summon": _gen_module_summon,
}


# ---------- 入口判定 ----------

def is_enterable(player, realm: dict) -> bool:
    """秘境是否可进入：已解锁（对话/动作）且境界在门槛区间内。"""
    if realm.get("id") not in player.secret_unlocked:
        return False
    order = curriculum.realm_order(player.realm_key)
    if order < curriculum.realm_order(realm.get("min_realm", "")):
        return False
    max_realm = realm.get("max_realm")
    if max_realm and order > curriculum.realm_order(max_realm):
        return False
    return True


# ---------- 挑战生成与自检 ----------

def generate_challenge(realm_id: str, rng: random.Random | None = None) -> dict:
    """生成一个秘境挑战；参考答案必须通过沙箱自检，否则重新生成。"""
    realm = get_realm(realm_id)
    if not realm:
        raise ValueError("秘境不存在：" + realm_id)
    rng = rng or random.Random()
    last_error = None
    for _ in range(8):
        template_id = rng.choice(realm["templates"])
        generator = _GENERATORS.get(template_id)
        if generator is None:
            continue
        task = generator(rng)
        task.update({
            "id": "secret:" + realm_id,
            "kind": "secret",
            "realm": None,
            "title": "秘境 · " + task["title"],
            "reward": int(realm.get("reward", {}).get("cultivation", 80)),
            "rewards": realm.get("reward", {}),
            "no_solution": True,
            "secret_realm": realm_id,
            "time_limit": 5,
        })
        outcome = tasks.validate_task(task, task["solution"])
        if outcome.passed:
            return task
        last_error = outcome
    raise RuntimeError("秘境试炼自检失败，请稍后再试。" + (str(last_error.run.message) if last_error else ""))


def sanitize(task: dict) -> dict:
    """对外任务数据：不暴露参考答案与验证结构。"""
    keys = ("id", "kind", "title", "story", "hints", "starter_code",
            "no_solution", "secret_realm", "time_limit")
    return {k: task.get(k) for k in keys if k in task}


def apply_clear(player, realm_id: str, task: dict) -> dict:
    """结算通关：发放奖励（首通/重复），记录秘境历练次数。"""
    realm = get_realm(realm_id)
    if not realm:
        raise ValueError("秘境不存在：" + realm_id)
    cleared = int(player.secret_log.get(realm_id, 0))
    reward_cfg = realm.get("reward", {}) if cleared == 0 else realm.get("repeat_reward", {})
    reward_task = {
        "reward": int(reward_cfg.get("cultivation", 0)),
        "rewards": reward_cfg,
    }
    details = tasks.apply_rewards(player, reward_task)
    player.secret_log[realm_id] = cleared + 1
    return {
        "secret_cleared": realm_id,
        "cleared_count": player.secret_log[realm_id],
        "first_clear": cleared == 0,
        "rewards": details,
    }