# 《码上飞升：青云宗篇》Godot 开发日志

## 项目约束

- 引擎：Godot 4.x，当前开发验证版本为 4.7.1-stable。
- 形态：2.5D 俯视角单机 RPG Demo。
- 范围：青云宗第一章，不修改 Web Edition 核心代码与数据格式。
- 流程：实现 → 测试 → 修复 → 更新日志 → 提交 → 下一阶段。

## G0 · 项目初始化与技术架构（2026-08-08）

### 完成内容

- 建立独立 `godot/` 项目、目录结构、项目图标和运行说明。
- 建立 `EventBus`、`DataRepository`、`GameState`、`SaveManager`、`SceneRouter` 五个 Autoload。
- 建立深青水墨风标题场景及新游戏、继续、退出入口。
- 建立首章世界、NPC、对话、功法、挑战和剧情 JSON 骨架。
- 建立独立 `user://saves/` 存档边界，不接触 Web Edition 存档。
- 使用官方 Godot 4.7.1 Windows 便携版作为本地开发工具，工具位于被忽略的 `.tools/`。

### 技术决策

- 世界逻辑使用 Godot 2D 节点，通过 Y 排序、遮挡、阴影和视差形成 2.5D 观感。
- 游戏状态与 UI 使用信号解耦；数据使用稳定 ID 的 JSON 驱动。
- 玩家 Python 代码不由 GDScript 判定，后续通过独立桥接进程真实隔离执行。
- 原型阶段使用程序化占位资源，玩法闭环通过后再集中替换美术。

### 测试结果

- `Godot --headless --editor --path godot --quit`：通过，项目扫描、Autoload 注册与资源导入无错误。
- `Godot --headless --path godot --quit-after 3`：通过，主场景启动并输出版本标识。

### 当前问题

- 本机原先未安装 Godot，已在 `.tools/godot/` 配置便携版，不影响仓库和系统环境。
- 当前仅为可运行工程骨架，角色创建和世界探索将在 G1 实现。

### 下一步

- G1：实现角色创建、玩家控制、摄像机、青云宗五处地点、交互提示与位置存档。
