# -*- coding: utf-8 -*-
"""AI 师尊系统（见 docs/V0.2_DESIGN.md §3.3）。

独立 Provider 架构：
- base.TutorProvider：统一接口（guidance / error_analysis）；
- local_tutor.LocalTutor：默认本地规则引擎（离线可用，无需密钥）；
- openai_tutor.OpenAICompatibleTutor：可选 OpenAI 兼容 HTTP 模型。

铁律：AI 不替玩家解题。提示等级 1 方向 → 2 缩小 → 3 明确线索 → 4 查看答案。
"""

from __future__ import annotations

from .base import TutorProvider
from .local_tutor import LocalTutor
from .openai_tutor import OpenAICompatibleTutor


def create_tutor() -> TutorProvider:
    """创建导师：配置了 AI 密钥则用外部模型，否则本地规则引擎。"""
    external = OpenAICompatibleTutor()
    if external.enabled():
        return external
    return LocalTutor()


def create_local_tutor() -> LocalTutor:
    return LocalTutor()


__all__ = ["TutorProvider", "LocalTutor", "OpenAICompatibleTutor", "create_tutor", "create_local_tutor"]
