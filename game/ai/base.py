# -*- coding: utf-8 -*-
"""导师 Provider 抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TutorProvider(ABC):
    """AI 师尊统一接口。未来接入不同模型只需实现本接口。"""

    name: str = "base"

    @abstractmethod
    def guidance(self, player, context: dict) -> str:
        """根据玩家状态与上下文生成分级提示文本。

        context 字段：
            task_id      当前任务 id
            title        任务标题
            hints        任务 hints 数组
            attempts     已提交失败次数
            hint_level   请求的提示等级（1-4）
            realm_key    当前境界
        """

    @abstractmethod
    def error_analysis(self, player, run: dict, task: dict | None = None) -> str:
        """对一次代码运行结果做引导式错误分析。

        run 为 sandbox.RunResult.to_dict() 结果。
        """
