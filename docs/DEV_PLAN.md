# 《码上飞升》V0.1 开发计划

> 文档状态：已执行完毕（本文件为开发前制定的计划，含执行结果备注）。

## 1. 项目目标

完成《码上飞升》V0.1（炼气期完整体验）：

凡人进入修仙世界 → 获得 Python 真解 → 学习基础 Python → 完成任务 → 解决 Bug（Debug）→ 通过测试 → 经历筑基天劫 → 成功筑基。

玩家必须通过**真实编写并运行 Python 代码**获得成长，禁止关键词匹配、禁止伪代码判定。

## 2. 技术路线

| 项目 | 选择 | 理由 |
| --- | --- | --- |
| 语言 | Python 3.10+ | 与教学内容同语言，简化沙箱实现 |
| 服务端 | Flask（REST API + 静态托管） | 轻量、零前端构建链、易测试 |
| 前端 | 原生 HTML/CSS/JS + CodeMirror 5 | 无需 Node 构建，离线可用，编辑器体验成熟 |
| 代码执行 | 子进程 `python -I -E -u -X utf8` + 沙箱内核 | 真实执行 + 隔离 + 超时/内存限制 |
| 存档 | JSON 文件（`saves/`，原子写入） | 简单可读、便于调试与测试隔离 |
| 数据 | JSON（`game/data/`，UTF-8） | 课程/任务数据与代码分离，可扩展 |
| 测试 | pytest + playwright-core E2E | 单元/集成/端到端全覆盖 |
| 发布 | zipapp 单文件 + Windows 启动脚本 | 保持沙箱可用（复用宿主 Python），免打包器依赖 |

关键约束：玩家代码沙箱通过 `sys.executable` 复用宿主 Python 解释器，因此发行包不采用 PyInstaller 冻结打包，而采用 zipapp。

## 3. 开发阶段划分

| 阶段 | 目标 | 交付物 |
| --- | --- | --- |
| 阶段 0 初始化 | 环境勘察、方案确定、目录与仓库初始化 | 目录结构、配置文件、本计划 |
| 阶段 1 沙箱 | 可安全真实执行玩家代码 | `game/sandbox.py`、`game/sandbox_bootstrap.py` |
| 阶段 2 课程数据 | 境界、任务、炼丹房、天劫数据结构 | `game/data/curriculum.json`、`game/data/tasks.json` |
| 阶段 3 玩家与存档 | 玩家状态与存取档 | `game/player.py`、`game/save.py` |
| 阶段 4 任务系统 | 真实执行验证 + 进度推进 | `game/tasks.py` |
| 阶段 5 服务端 API | 游戏状态/任务/运行/提交/突破接口 | `game/server.py` |
| 阶段 6 前端 | 完整游戏界面 | `static/`（标题、建角、洞府、任务、渡劫台、完成） |
| 阶段 7 完整流程 | 炼气期闭环：学习→任务→Debug→天劫→筑基 | `tests/test_playthrough.py` |
| 阶段 8 测试与 E2E | 回归保障 + 真实浏览器验证 | `tests/`、`scripts/e2e_test.js` |
| 阶段 9 发布 | 可分发产物与文档 | `scripts/build.py`、`docs/*`、`DEVLOG.md` |

## 4. 每阶段验收要点

- 阶段 1：语法错误、运行错误、超时（无限循环）、内存超限、危险模块屏蔽均有测试覆盖。
- 阶段 4：任务验证为**真实执行比对**（output 精确/包含比对、function 用例比对），无关键词匹配。
- 阶段 7：`test_full_playthrough_to_foundation` 一次性打通凡人→筑基全流程。
- 阶段 8：E2E 覆盖标题→建角→地图→任务→运行→错误提交→正确提交→突破→教学渲染→炼丹房→渡劫台→筑基→存档继续→完成界面。
- 阶段 9：`python scripts/build.py` 产出 zipapp 并对发行包做启动冒烟验证（首页/静态/API/沙箱/提交/课程数据）。

## 5. 风险分析

| 风险 | 等级 | 应对 |
| --- | --- | --- |
| 玩家代码无限循环/内存爆炸 | 高 | 子进程超时强杀；Windows Job Object 内存上限 + 轮询监控；POSIX setrlimit |
| 沙箱逃逸（进程内无法根除） | 中 | `-I` 隔离模式 + 危险模块/内建屏蔽 + 临时 cwd + 最小环境变量；教学场景可接受，文档明示 |
| Python 3.13 导入机制依赖 `_io.open` | 中 | 标准库目录白名单守卫，允许解释器自举读取标准库 |
| 输出伪造干扰验证 | 低 | 随机 marker 解析结果，玩家输出无法伪造 |
| 中文编码（Windows 管道/控制台） | 中 | 全部文件 UTF-8；测试脚本避免管道写中文；文档统一 UTF-8 |
| 打包后资源路径失效 | 中 | zipapp 模式通过 `importlib.resources` 读取数据与静态资源 |

## 6. 测试方案

- 单元/集成：`python -m pytest tests -q`（沙箱、任务、API、完整通关）。
- 端到端：`node scripts/e2e_test.js`（系统 Chrome 无头，playwright-core）。
- 构建验证：`python scripts/build.py`（构建 + 发行包冒烟验证）。
- 测试隔离：pytest 通过夹具将存档目录指向临时目录，不污染真实存档。

## 7. 预计实现顺序

环境勘察 → 沙箱 → 课程数据 → 玩家/存档 → 任务系统 → API → 前端 → 完整通关测试 → E2E → 发布构建 → 文档 → 回归。

## 8. 执行结果

- 全部 89 项 pytest 通过（14 项按平台跳过），E2E 全部检查通过。
- 发行包构建与冒烟验证通过，`启动游戏.bat` 实测可拉起游戏。
- 详细证据见 `docs/TEST_REPORT.md` 与 `docs/ACCEPTANCE.md`。
