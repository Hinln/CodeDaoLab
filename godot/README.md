# CodeDaoLab Godot Edition

当前版本：**v0.2.1 新手引导增强版**

《码上飞升：青云宗篇》是一款把真实 Python 编程变成修仙施法过程的 2.5D RPG。Godot Edition 与 Web Edition 独立存在，使用独立存档，但复用经过验证的 Python 沙箱核心。

## 第一章流程

创建道号、灵根与身份 -> 循世界灵光进入青云宗 -> 拜见 NPC -> 修习真言诀、变量吐纳诀、循环周天诀 -> 以真实 Python 破除三阶段 Bug 妖 -> 引气入体 -> 查看个性化章节结算。

## V0.2 增强

- 观题、落笔、起式、运转、显化、命中/反噬代码施法链。
- 语法断裂、运行反冲、超时冻结、输出偏移和环境失联差异化反馈。
- 世界目标地点、距离、灵光和青玄子传音引导。
- 五灵根、三身份背景及持久化角色差异。
- 三名 NPC 的程序化立绘、表情、记忆和关系阶段。
- 五地点动态天气、程序化环境音和一次性观察点。
- 三门功法的入门、运转、小成节点与掌握证据。
- 三阶段概念驱动 Bug 妖表现。
- 保存失败历史、但不保存源码的师尊伙伴系统。
- 灵根突破阵纹、关系回顾和个性化章节评语。

## V0.2.1 新手引导增强

- `WASD` 与方向键均可移动，靠近人物或地点后按 `E` 交互。
- 首次进入世界自动打开四步修行指引，顶部“指引”按钮可随时重开。
- 任务卡同时显示目标方向、距离和抵达后的交互按键。
- 代码试炼使用编号步骤区分“运行观察”与“提交验证”。
- 输出不一致时展示目标/实际逐字符对照，并能精确指出遗漏的中文句号。
- Boss 战固定显示“观察、诊断、修改、攻击”破招流程。
- `Ctrl+Enter` 快速运行，`Ctrl+Shift+Enter` 快速提交验证。

## 运行源码

使用 Godot 4.7.1 打开 `project.godot`，或在仓库根目录执行：

```powershell
.tools\godot\Godot_v4.7.1-stable_win64.exe --path godot
```

代码试炼需要系统安装 Python 3.10+。可通过环境变量 `CODEDAO_PYTHON` 指定解释器。

## 测试与发布

```powershell
godot\scripts\run_tests.ps1
godot\scripts\build_release.ps1
```

统一测试包含 212 项 Godot 检查，其中 15 项验证新手引导，8 项使用超长文本压力测试全部玩家界面的视口边界。构建脚本还会验证发布目录中的 Python 判题和 Godot 运行时，再生成 Windows ZIP。

## 文档

- `docs/V0.2_REVIEW.md`：产品体验评审。
- `docs/V0.2_DESIGN.md`：体验设计。
- `docs/V0.2_ART_DIRECTION.md`：美术与声音规范。
- `docs/ACCEPTANCE.md`：最终验收。
- `docs/TEST_REPORT.md`：测试结果。
- `docs/RELEASE.md`：发布说明。
