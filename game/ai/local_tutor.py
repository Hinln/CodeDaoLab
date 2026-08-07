# -*- coding: utf-8 -*-
"""本地规则引擎导师（默认实现，离线可用）。

规则：
- 提示分级：L1 方向提示 → L2 范围缩小 → L3 明确线索 → L4 查看答案；
- 悟性影响分级节奏（高悟性更快获得更细线索）；
- 心境低时增加鼓励话术；
- 错误归因：语法/运行/超时/内存/输出不符各有专属引导；
- 语言风格随境界调整（低境界白话教学腔，高境界修仙黑话）。
"""

from __future__ import annotations

from .. import curriculum
from .base import TutorProvider


class LocalTutor(TutorProvider):
    name = "local"

    # ---------- 提示分级 ----------

    def level_for(self, player, attempts: int) -> int:
        """计算当前应提供的提示等级（1-4）。"""
        base = 1
        if attempts >= 3:
            base = 3
        elif attempts >= 2:
            base = 2
        # 悟性：>=20 悟性时每 2 次失败可跳过一级
        if player.comprehension >= 20 and attempts >= 2:
            base = min(3, base + 1)
        # 心境过低时不让玩家挫败：直接给到 L3 线索
        if player.mindset <= 30:
            base = max(base, 3)
        return min(4, max(1, base))

    def guidance(self, player, context: dict) -> str:
        attempts = int(context.get("attempts", 0) or 0)
        req_level = int(context.get("hint_level", 0) or 0)
        level = min(4, req_level) if req_level else self.level_for(player, attempts)
        hints = context.get("hints") or []
        title = context.get("title") or "当前任务"
        style = self._style(player)

        if level >= 4:
            if context.get("no_solution"):
                return (
                    style["open"] + "此乃试炼，为师不会替你把参考答案摆出来。"
                    "回到『功法讲解』，把每一则示例亲手敲一遍，拆解题意，再试一次。"
                    "试炼的意义，在于你亲手破关。" + style["close"]
                )
            return (
                style["open"] + "这一关的「参考答案」就在任务页右下角的『查看参考答案』处。"
                "但为师劝你：先合上答案，自己再试一次。心魔，须亲手斩之。" + style["close"]
            )

        if level == 1:
            return (
                style["open"] + "先别急着写。想一想：这一关要『输出什么』、『输入是什么』。"
                "把题目拆成小步，每一步都先用 print 验证。方向对了，路就通了一半。" + style["close"]
            )

        if level == 2:
            line = hints[0] if hints else "回顾这一境界的功法讲解，找到关键概念。"
            if len(hints) >= 2:
                line += "再进一步：" + hints[1]
            return style["open"] + "为师给你缩小范围：\n\n" + line + style["close"]

        # L3：明确线索
        line = hints[1] if len(hints) >= 2 else (hints[0] if hints else "再看一遍题目与功法示例。")
        if len(hints) >= 3:
            line += "\n\n最后一层线索：" + hints[2]
        return (
            style["open"] + "「" + title + "」的破局之钥在此：\n\n" + line +
            "\n\n若仍不解，再向为师求『明确线索』或直接查看参考答案（L4）。" + style["close"]
        )

    # ---------- 错误分析 ----------

    def error_analysis(self, player, run: dict, task: dict | None = None) -> str:
        status = run.get("status", "ok")
        style = self._style(player)
        encourag = "莫要灰心，Bug 即心魔，破之即成长。" if player.mindset <= 50 else "再接再厉。"

        if status == "syntax":
            line = run.get("error_line") or "？"
            return (
                style["open"] + "心魔是『语法之障』：第 " + str(line) + " 行附近有语法错误。"
                "常见原因：引号没闭合、括号不配对、冒号漏写、缩进错乱。"
                "逐字对照功法示例检查一遍。" + encourag + style["close"]
            )
        if status == "runtime":
            cls = run.get("error_class") or "异常"
            return (
                style["open"] + "运行之时出了岔子：「" + str(cls) + "」。"
                "先看报错最后一行提示的出错位置，再想该行用到的变量/函数是否已定义、类型是否匹配。"
                + encourag + style["close"]
            )
        if status == "timeout":
            return (
                style["open"] + "此乃『无限循环』心魔：程序超过时限被强行中断。"
                "检查循环条件是否会一直为真：循环体内是否更新了控制变量？是否有 break 出口？"
                + encourag + style["close"]
            )
        if status == "memory":
            return (
                style["open"] + "灵力枯竭（内存超限）。多半是循环无限追加数据所致。"
                "检查是否在循环里不断往列表/字符串添加内容。" + encourag + style["close"]
            )
        if status == "ok":
            return (
                style["open"] + "运行无碍，但验证未过——输出与预期不符。"
                "把『灵台输出』与题目要求的输出逐字对比：内容、顺序、空行、标点都算数。"
                + encourag + style["close"]
            )
        return style["open"] + "情况有些复杂，先看灵台输出，再逐段代码自查。" + style["close"]

    # ---------- 风格 ----------

    def _style(self, player) -> dict:
        order = curriculum.realm_order(player.realm_key)
        if order <= 4:
            return {"open": "青玄子捋须笑道：「", "close": "」"}
        if order <= 8:
            return {"open": "青玄子颔首：「", "close": "」"}
        return {"open": "青玄子双目微阖，传音入密：「", "close": "」"}
