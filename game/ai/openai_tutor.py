# -*- coding: utf-8 -*-
"""OpenAI 兼容 HTTP 导师（可选）。

启用方式（环境变量）：
    CA_AI_BASE_URL=https://api.openai.com/v1
    CA_AI_API_KEY=sk-...
    CA_AI_MODEL=gpt-4o-mini

未配置或请求失败时自动回退到本地规则引擎，保证游戏始终可用。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import TutorProvider
from .local_tutor import LocalTutor

SYSTEM_PROMPT = """你是《码上飞升》修仙世界中的授业师尊「青玄子」。
玩家正在通过真实编写 Python 代码推进修仙剧情。
你的职责是引导式教学，铁律如下：
1. 绝不直接给出完整答案代码，除非玩家明确请求 L4（查看答案）。
2. 提示分级：L1 方向提示（宏观思路）→ L2 范围缩小（指出相关概念/步骤）→ L3 明确线索（接近答案的具体提示）→ L4 查看答案。
3. 先分析玩家代码/运行错误，再给针对性提示；语言简洁、有修仙风味但不堆砌。
4. 玩家连续失败时先鼓励，再给线索。
5. 根据玩家境界调整语气：低境界（凡人~炼气）用平实教学话，高境界可用修仙术语。"""


class OpenAICompatibleTutor(TutorProvider):
    name = "openai-compatible"

    def __init__(self):
        self.base_url = (os.environ.get("CA_AI_BASE_URL") or "").rstrip("/")
        self.api_key = os.environ.get("CA_AI_API_KEY") or ""
        self.model = os.environ.get("CA_AI_MODEL") or "gpt-4o-mini"
        self._fallback = LocalTutor()

    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _chat(self, user_message: str) -> str | None:
        if not self.enabled():
            return None
        url = self.base_url + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.6,
            "max_tokens": 400,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

    def guidance(self, player, context: dict) -> str:
        level = context.get("hint_level") or context.get("attempts", 0) or 1
        msg = (
            f"玩家境界：{context.get('realm_key', player.realm_key)}，悟性 {player.comprehension}，心境 {player.mindset}。\n"
            f"当前任务：{context.get('title', '')}\n"
            f"官方提示（供你参考，不要直接复述全部）：{json.dumps(context.get('hints', []), ensure_ascii=False)}\n"
            f"玩家已尝试失败次数：{context.get('attempts', 0)}\n"
            f"请提供 L{min(4, max(1, level))} 级提示。"
        )
        text = self._chat(msg)
        if text:
            return "青玄子传音入密：「" + text + "」"
        return self._fallback.guidance(player, context)

    def error_analysis(self, player, run: dict, task: dict | None = None) -> str:
        msg = (
            f"玩家境界：{player.realm_key}，心境 {player.mindset}。\n"
            f"运行结果：{json.dumps(run, ensure_ascii=False)}\n"
            f"任务：{json.dumps(task or {}, ensure_ascii=False)[:800]}\n"
            "请以引导式口吻分析这段输出对应的代码问题，并给出 1-2 条针对性线索（不要直接给完整答案）。"
        )
        text = self._chat(msg)
        if text:
            return "青玄子传音入密：「" + text + "」"
        return self._fallback.error_analysis(player, run, task)
