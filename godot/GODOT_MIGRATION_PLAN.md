# 《码上飞升：青云宗篇》Godot 迁移方案

> 目标引擎：Godot 4.x  
> 产品形态：2.5D 俯视角单机 RPG Demo  
> 迁移原则：Web Edition 保持不变；Godot Edition 仅在 `godot/` 内开发；先占位资源打通玩法，再按美术规范替换。

## 1. Web 系统与 Godot 系统对应关系

| Web Edition | Godot Edition | 迁移策略 |
| --- | --- | --- |
| Flask `server.py` 状态聚合 | `GameState` Autoload | 将第一章所需状态放入内存模型，信号驱动 UI 刷新 |
| `player.py` | `PlayerProfile` Resource + `GameState` | 保留道号、境界、修为、悟性、心境、位置、功法和剧情标记 |
| `save.py` 多槽位 JSON | `SaveManager` Autoload | 独立保存到 `user://saves/`，不读取或覆盖 Web 存档 |
| `world.json` / `world.py` | `WorldData` + 青云宗场景 | 五处首章地点改为可自由移动的 2.5D 空间；触发区承担地点入口 |
| `npcs.json` / `dialogues.json` | `NpcActor` + `DialogueManager` | NPC 作为场景实体，交互触发数据驱动对话与任务动作 |
| `story.json` / `story.py` | `QuestManager` | 将第一章拆为有序剧情节点，条件和奖励由动作白名单执行 |
| `techniques.json` / `techniques.py` | `TechniqueManager` | 首章实现真言诀、变量吐纳诀、循环周天诀及熟练度 |
| `tasks.py` / `sandbox.py` | `PythonBridge` + 独立桥接进程 | 玩家代码仍由隔离 Python 子进程真实执行，Godot 只消费 JSON 结果 |
| `ai/` | `TutorManager` | 默认本地分级提示；仅在接口可用时接入外部模型，不影响离线流程 |
| 浏览器 CodeMirror | Godot `CodeEdit` | 提供代码输入、运行输出、提交验证、提示和错误定位 |
| 卡片地图 | 2.5D 俯视角场景 | 玩家可行走、镜头跟随、靠近 NPC/地点后交互 |
| 成就/图鉴/贡献面板 | 首章 HUD 与日志页 | Demo 只展示流程需要的任务、属性、功法和存档反馈，不扩张完整长期系统 |

## 2. 数据迁移方案

### 2.1 数据边界

- Web 数据保持原格式和原路径，不修改 `game/data/`。
- Godot 在 `godot/data/` 维护首章运行所需的精简 JSON 快照。
- JSON 使用稳定 ID 关联，显示名称仅用于 UI，禁止以中文名称作为逻辑主键。
- Godot 数据加载失败时给出明确错误并停止进入游戏，不静默创建错误状态。

### 2.2 首章数据集

| 文件 | 内容 |
| --- | --- |
| `data/world.json` | 山门、洞府、藏经阁、演武场、后山入口；出生点、碰撞边界、传送点、交互点 |
| `data/npcs.json` | 青玄子、玄机长老、云游子的位置、称号、对话树入口 |
| `data/dialogues.json` | 拜师、授法、试炼、后山警示等节点与白名单动作 |
| `data/techniques.json` | 真言诀、变量吐纳诀、循环周天诀及首章修炼条件 |
| `data/challenges.json` | 入门真言、变量试炼、循环试炼、Bug 妖战斗挑战 |
| `data/chapter_01.json` | 创建角色到突破炼气境的剧情节点、条件、目标和奖励 |

### 2.3 玩家与存档结构

```json
{
  "version": 1,
  "player": {
    "dao_name": "",
    "spirit_root": "wood",
    "realm": "mortal",
    "cultivation": 0,
    "comprehension": 10,
    "mindset": 100,
    "position": {"map": "qingyun_sect", "x": 0, "y": 0},
    "techniques": {},
    "quest_flags": {},
    "boss_defeated": false
  },
  "meta": {
    "saved_at": "",
    "chapter": 1
  }
}
```

- 存档写入采用临时文件后替换，避免中途退出造成损坏。
- 读取时校验 `version` 和关键字段，未知字段忽略，缺失字段补默认。
- 代码内容不写入永久存档，仅保存挑战完成状态。

## 3. 场景设计

### 3.1 主场景

```text
Main
├── WorldRoot
│   └── QingyunSect
├── Player
├── Camera2D
├── CanvasLayer
│   ├── HUD
│   ├── DialoguePanel
│   ├── CodeChallengePanel
│   ├── TechniquePanel
│   ├── QuestPanel
│   └── PauseMenu
└── TransitionLayer
```

### 3.2 场景文件

| 场景 | 职责 |
| --- | --- |
| `scenes/main/Main.tscn` | 装配世界、玩家、UI 与全局流程 |
| `scenes/menu/TitleScreen.tscn` | 新游戏、继续游戏、退出 |
| `scenes/menu/CharacterCreation.tscn` | 道号与灵根选择 |
| `scenes/world/QingyunSect.tscn` | 青云宗 2.5D 首章地图与五处地点 |
| `scenes/actors/Player.tscn` | 角色移动、动画占位、交互探测 |
| `scenes/actors/NpcActor.tscn` | NPC 通用实体与对话入口 |
| `scenes/ui/DialoguePanel.tscn` | 数据驱动对话与选项 |
| `scenes/ui/CodeChallengePanel.tscn` | `CodeEdit`、输出、运行、提交、提示 |
| `scenes/ui/Hud.tscn` | 属性、当前任务、交互提示 |
| `scenes/battle/BugBossArena.tscn` | Bug 妖阶段战与代码修复反馈 |

### 3.3 2.5D 表现

- 世界逻辑使用 2D：`CharacterBody2D`、`Camera2D`、碰撞层和 `Area2D`。
- 通过 Y 排序、前景遮挡、斜向地面、多层阴影与视差云雾形成 2.5D 观感。
- 第一版地图、角色和 NPC 使用 Godot 原生图形与程序化占位资源，不提前生成大量素材。
- 键盘支持 WASD/方向键，交互键为 E，Esc 打开暂停菜单。

## 4. 脚本架构

### 4.1 Autoload

| 脚本 | 职责 |
| --- | --- |
| `scripts/core/game_state.gd` | 玩家状态、当前任务、剧情状态及统一信号 |
| `scripts/core/data_repository.gd` | JSON 加载、结构检查、ID 查询 |
| `scripts/core/save_manager.gd` | 独立 Godot 存档、原子写入与恢复 |
| `scripts/core/scene_router.gd` | 标题、建角、世界和 Boss 场景切换 |
| `scripts/core/event_bus.gd` | UI、世界、任务之间的低耦合信号 |
| `scripts/python/python_bridge.gd` | 调用 Python 桥接进程并解析结果 |

### 4.2 领域脚本

- `player_controller.gd`：输入、移动、交互锁定、动画方向。
- `npc_actor.gd`：NPC 数据绑定、可交互状态、头顶提示。
- `dialogue_manager.gd`：节点跳转、条件过滤、动作白名单。
- `quest_manager.gd`：第一章节点推进、目标判断、奖励结算。
- `technique_manager.gd`：功法习得、熟练度与挑战入口。
- `bug_boss_controller.gd`：Boss 阶段、生命值、错误类型与代码挑战联动。
- `tutor_manager.gd`：L1 至 L4 提示，遵守“引导 > 提示 > 解释 > 答案”。

### 4.3 Python 执行桥

- Godot 不直接解释或判断 Python 代码。
- `python_bridge.gd` 将挑战 ID、玩家代码和操作类型写入临时 JSON。
- `python_bridge/runner.py` 读取请求，调用隔离执行层，输出单个 JSON 响应文件。
- 执行层必须具备超时、独立临时目录、危险模块限制和结构化错误。
- 挑战通过依据为输出或测试用例真实结果，禁止关键词扫描。
- Windows Demo 首版允许依赖系统 Python 3.10+，发布说明必须明确；后续再评估内嵌解释器。

## 5. 资源规划

### 5.1 原型期

- 地图：Polygon2D、TileMapLayer 或简单 Sprite2D 色块。
- 玩家/NPC：统一比例的程序化胶囊或剪影占位。
- UI：Godot Theme + 九宫格面板，建立青玉、宣纸、墨色、金色四类设计变量。
- 音频：首版允许静音运行，保留 AudioStreamPlayer 节点和总线结构。

### 5.2 美术替换期

- 统一方向：东方修仙、水墨幻想、青山云海、古建筑、灵光、2.5D。
- 优先级：地图地标 > 玩家与三名 NPC > UI 框体与图标 > Bug 妖 > 环境特效。
- 同类资源必须统一视角、光向、比例和描边，避免混用写实、像素与二次元立绘。
- AI 生成素材进入项目之前必须人工检查版权、透明边缘、分辨率和风格一致性。

## 6. 开发阶段

### G0：工程初始化

- 建立目录、`project.godot`、Autoload、标题页和启动场景。
- 验收：Godot 4 可导入并启动，无解析错误。

### G1：角色与世界

- 玩家控制、摄像机、碰撞、五处青云宗地点、交互提示、独立存档。
- 验收：可从山门行走至洞府、藏经阁、演武场和后山入口，保存后恢复位置。

### G2：NPC 与剧情

- 三名 NPC、对话、任务系统和第一章节点。
- 验收：创建角色后进入宗门、拜见青玄子、接取第一门功法任务。

### G3：功法与 Python 修炼

- 三门功法、CodeEdit 界面、真实 Python 运行与提交、分级提示。
- 验收：错误代码不推进，正确代码获得功法与修为。

### G4：Bug 妖战斗

- Boss 场景、分阶段 Bug 修复、战斗反馈和失败重试。
- 验收：至少三阶段代码斗法，修复全部错误后击败 Boss。

### G5：第一章整合

- 串联创建角色 → 入宗 → NPC → 功法 → 试炼 → Boss → 炼气突破。
- 验收：新存档可完整通关，读档可继续，关键状态无重复奖励。

### G6：美术、测试与发布

- 按风格指南替换关键占位资源、补充音频与特效、自动化测试和 Windows 导出配置。
- 验收：项目可运行、第一章完整、移动/NPC/存档/功法/Boss 全通过，生成 Windows Demo 或提供明确导出步骤。

## 7. 风险与控制

| 风险 | 控制措施 |
| --- | --- |
| Godot 与 Python 进程通信阻塞主线程 | 桥接调用使用异步线程/轮询，UI 显示运行状态并禁止重复提交 |
| 导出包缺少 Python | 首版明确系统 Python 依赖，启动时检测并给出可操作提示 |
| Web 数据与 Godot 数据漂移 | 仅迁移首章必要字段，记录来源版本，提供数据结构测试 |
| 剧情动作任意执行 | 使用固定动作白名单，不从 JSON 执行脚本或表达式 |
| 范围膨胀 | 只制作青云宗五处地点、三名 NPC、三门功法、一个 Bug 妖和第一章闭环 |
| 美术阻塞玩法 | G0 至 G5 使用占位资源，玩法验收通过后才集中替换 |

## 8. 完成定义

- Godot 4.x 项目可启动并完成第一章主流程。
- 玩家可在 2.5D 青云宗自由移动并与三名 NPC 交互。
- 三门功法和 Bug 妖战斗都由真实 Python 执行结果驱动。
- 存档、任务、功法、Boss 状态可正确恢复。
- Web Edition 文件与数据格式未被修改。
- `godot/DEVLOG.md` 记录每个阶段的实现、测试、问题和下一步。
- 重要阶段均有独立 Git Commit，所有开发位于 `feature/godot-edition`。
