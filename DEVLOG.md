# 《码上飞升》开发日志

## 项目概况

- 项目：码上飞升（Code Ascension）V0.2
- 定位：东方修仙世界观下的 Python 编程学习 RPG
- 核心理念：代码即修行；Bug 是心魔；Debug 是破境；项目是历练
- 当前状态：**V0.2.5 产品打磨已完成（六阶段全部完成，pytest 239 通过 / E2E 31 项通过 / 发行构建冒烟 9/9）**
- 版本：v0.2.5

---

## 开发时间线

### 阶段 0 · 项目初始化（2026-08-07）

- 完成：环境勘察（Windows 11 / Python 3.13 / Node 24 / Chrome 可用）、技术方案确定、目录结构创建、git 仓库初始化、`requirements.txt` / `.gitignore` / 启动入口 `run.py`。
- 技术决策：
  - Flask 后端 + 原生 JS 前端（无构建链），保证离线可运行、易维护。
  - 代码编辑器选用 CodeMirror 5（本地 vendor 文件，不依赖 CDN）。
  - 测试框架 pytest；E2E 用 playwright-core + 系统 Chrome。
- 产出：《码上飞升 V0.1 开发计划》（`docs/DEV_PLAN.md`）。

### 阶段 1 · Python 沙箱（核心难点）

- 完成：`game/sandbox.py` + `game/sandbox_bootstrap.py`。
- 设计：
  - 玩家代码在独立子进程 `python -I -E -u -X utf8` 中**真实编译执行**，代码经 stdin 传入，cwd 为全新临时目录，环境变量最小化。
  - 超时（5 秒）防无限循环；Windows 用 Job Object 内存上限 + 轮询监控（POSIX 用 setrlimit）。
  - 危险模块/内建屏蔽；`open` 类函数改为标准库目录白名单守卫（修复 Python 3.13 导入机制依赖 `_io.open` 导致的崩溃）。
  - 随机 marker 解析结果，玩家输出无法伪造验证结果。
- 踩坑记录：
  - PowerShell 管道写中文文件易损坏 → 一律改为文件内写好脚本再执行、逐文件写盘。
  - 沙箱语法错误格式化必须返回 dict；`error_line` 需扣除 `lstrip("\n")` 偏移。
- 测试：`tests/test_sandbox.py` 27 项通过。

### 阶段 2 · 课程数据

- 完成：`game/data/curriculum.json`（12 境界：凡人→炼气一~十层→筑基）、`game/data/tasks.json`（18 任务）。
- 结构：境界含教学（teaching/intro）；任务按 kind 分 main/debug/wave；debug 按境界解锁；天劫 3 波次。
- 验收对齐：Hello World/变量/条件/循环/函数/Debug 全部覆盖。

### 阶段 3 · 玩家与存档

- 完成：`game/player.py`（Player 状态模型）、`game/save.py`（JSON 存档，原子写入，utf-8-sig 读取，槽位名白名单防路径穿越）。

### 阶段 4 · 任务系统

- 完成：`game/tasks.py`。验证原则：**绝无关键词匹配**。
  - output 模式：真实运行后规范化输出与预期精确/包含比对。
  - function 模式：沙箱内以用例驱动函数调用并逐项比对。
  - 进度推进：主线/炼丹房/天劫三类完成逻辑、突破资格判定、天劫解锁。

### 阶段 5 · 服务端 API

- 完成：`game/server.py`（REST API：state/new/save/load/curriculum/tasks/run/submit/breakthrough）+ 静态托管。
- 测试：`tests/test_api.py` 10 项通过。

### 阶段 6 · 前端

- 完成：`static/` 全部界面：标题、建角（道号+灵根）、洞府地图、任务页（剧情/教学/提示/参考答案 + CodeMirror 编辑器 + 运行/提交）、突破弹窗、渡劫台、筑基完成页。
- 修复：任务页早期缺 `id="solution-row"` 导致 `openTask` 报错。

### 阶段 7 · 完整流程测试

- 完成：`tests/test_playthrough.py`：凡人→全部主线→Debug→三道天劫→筑基→存档恢复全流程验证；错误代码不推进进度。

### 阶段 8 · E2E 与截图

- 完成：`scripts/e2e_test.js`，14 项浏览器流程检查全部通过。
- 截图：`.tools/shots/01-title.png` ~ `08-tribulation.png`（视觉 QA 素材）。

### 阶段 9 · Release 构建与文档

- 完成：`scripts/build.py`（zipapp 单文件 + `启动游戏.bat` + `运行说明.txt` + 发行包冒烟验证 8/8）。
- 完成：zipapp 兼容改造（`config.py`/`curriculum.py`/`server.py` 通过 `importlib.resources` 读取归档内数据与静态资源；存档落用户数据目录，`CA_SAVE_DIR` 可覆盖）。
- 完成：`docs/DEV_PLAN.md`、`docs/USAGE.md`、`docs/TEST_REPORT.md`、`docs/ACCEPTANCE.md`。

---

## 最终测试结果（2026-08-07）

- pytest：**89 passed, 14 skipped**（跳过项为有意：非 Debug 任务不做心魔初始代码校验）。
- E2E：**ALL E2E CHECKS PASSED**（14 项）。
- 发行包冒烟验证：**8/8 PASS**；`启动游戏.bat` 实测通过。

---

## 技术决策记录

| 决策 | 选择 | 原因 |
| --- | --- | --- |
| 沙箱执行模型 | 子进程 `python -I` + 自研内核 | 真实执行 + 隔离 + 可控超时/内存 |
| 发行形态 | zipapp 而非 PyInstaller | 沙箱复用 `sys.executable`；免冻结打包器 |
| 静态资源读取 | 源码读磁盘 / 打包读归档（resources） | 两种形态共用一套代码 |
| 存档 | JSON 文件 | 简单、可读、可测试隔离 |
| 前端 | 原生 JS + CodeMirror 5 | 离线可用、依赖少 |
| 验证方式 | 真实执行比对（output/function 用例） | 杜绝关键词/伪代码判定 |

## 已知问题

1. 沙箱为进程级隔离，对抗性逃逸（类继承链内省等）无法完全根除；面向教学场景可接受，已在文档明示。
2. 单存档槽位（`default`），多槽位留待后续版本。
3. 前端无移动端深度适配（桌面优先）。
4. E2E 依赖本机 Chrome 与 Node，未纳入 CI。
5. 沙箱内存限制为进程级（Windows Job Object），多子进程场景仍需按单进程评估。

---

## V0.2 阶段二 · 架构升级（2026-08-07）

### 完成内容

- **玩家系统升级**：新增悟性/心境/Debug 经验属性、成就/道具/已学功法/NPC 标记/秘境记录字段；旧存档自动兼容（缺字段补默认）。
- **多存档系统**：`saves/{slot}.json` 多槽位；`GET /api/slots`、`POST /api/game/load?slot=`、`POST /api/game/delete`；前端标题页槽位列表 + 建角页槽位输入。
- **NPC 系统**：`game/data/npcs.json` + `game/npcs.py`，5 位 NPC（青玄子/玄机长老/丹尘子/云游子/小月），洞府地图 NPC 名片。
- **对话系统**：`game/data/dialogues.json` + `game/dialogues.py`，节点式对话树；动作：一次性奖励/解锁支线/解锁秘境/习得功法；前端对话弹窗（含结束按钮）。
- **任务系统升级**：新增支线任务类型（`branch`），2 个支线任务（采药奇遇 qi7 / 炼丹秘方 qi10）；任务支持前置境界（requires_realm）与结构化奖励（修为/悟性/Debug经验/道具）；验证引擎不变。
- **功法系统**：`game/techniques.py`，功法由境界教学派生；突破习得新功法；藏经阁页面浏览已参悟功法。
- **道具系统**：`game/data/items.json` + `game/items.py`，4 种道具（静心丹/清心丹/悟道丹/点拨灵符），储物袋面板 + 使用 API。
- **服务端**：新增 npcs/dialogues/techniques/items/slots API；`_build_state` 输出支线/功法/道具。

### 技术决策

- 支线解锁采用「NPC 动作解锁 + 数据前置境界」双层控制，兼顾剧情与数值门槛。
- 对话动作按 action id 对每个玩家只生效一次（防重复奖励）。
- 功法直接由课程数据派生，避免双份数据源。

### 遇到的问题

- E2E 点击全屏弹窗中心落在弹窗内容上导致无法关闭 → 对话弹窗增加明确的「结束对话」按钮。
- 储物袋最初渲染全部道具定义（含 0 数量）→ 改为只渲染已拥有道具。

### 测试

- 新增 `tests/test_v02_architecture.py` 16 项；全量 pytest 109 passed, 16 skipped。
- E2E 新增 5 项检查（地图扩展/藏经阁/对话/支线解锁/储物袋），合计 19 项全部通过。

## V0.2 阶段一 · 产品评审（2026-08-07）

- 完成：通读 V0.2 七阶段文档与 V0.1 核心文档，输出《码上飞升 V0.2 设计方案》（`docs/V0.2_DESIGN.md`）。
- 设计要点：
  - 八大系统：AI 师尊 / 属性系统 / 成就系统 / 功法体系 / 道具丹药 / NPC 与对话 / 支线任务 / 秘境历练。
  - 境界链扩展：凡人 → 炼气一~十层 → 筑基 → 后续预留（金丹/元婴……）；`curriculum.json` 引入 `major_realms` 大境界归属。
  - 技术架构：服务端保持 Flask + 数据驱动 JSON；AI 采用「本地规则引擎 + 可插拔模型 Provider」；存档 JSON 多槽位。
- 风险与对策：内容量放大 → 数据驱动 + 模板化；AI 依赖外部服务 → 本地回退；旧存档兼容 → 新字段全部带默认值。

## V0.2 阶段三 · AI 师尊系统（2026-08-07）

- 完成：`game/ai/`（`base.py` / `local_tutor.py` / `openai_tutor.py` / `__init__.py`）。
- 功能：
  - 提示分级：L1 方向 → L2 缩小范围 → L3 明确线索 → L4 参考答案；优先引导而非代答。
  - 悟性 ≥ 20 加速提示等级；心境 ≤ 30 直接给予 L3 线索（防挫败）。
  - 错误分析：`POST /api/ai/analyze` 真实运行玩家代码，按语法/运行/超时/结果不符分类归因，输出师尊式诊断。
  - 多模型兼容：环境变量 `CA_AI_BASE_URL` / `CA_AI_API_KEY` / `CA_AI_MODEL`；外部模型不可用时自动回退本地引擎。
- 测试：`tests/test_v02_ai.py` 19 项；全量 pytest 128 passed。

## V0.2 阶段四 · 游戏化增强（2026-08-08）

### 完成内容

- **属性系统**：悟性（加速师尊提示）、心境（失败 -2、成功 +2）、Debug 经验、连续通过 streak；提交失败记录 attempts。
- **大境界链**：`curriculum.json` 新增 `major_realms`（凡人/炼气/筑基……，qi1~qi10 归炼气，foundation 归筑基，后续预留）；`curriculum.py` 提供 `major_realm_for()` / `major_realm_order()`。
- **成就系统**：`game/data/achievements.json` 16 项成就 + `game/achievements.py` 条件引擎（task_done / realm_reached / count / cultivation_ge / debug_exp_ge / streak_ge / items_ge / flag / event）；解锁自动发奖（修为/悟性/Debug经验/道具）并授予称号。
- **游戏反馈**：任务提交 / 突破 / 对话 / 道具使用后返回 `new_achievements`；前端成就碑卡片、成就列表弹窗、解锁弹窗、地图称号展示（如「筑基真人」）。

### 技术决策

- 成就完全数据驱动，条件引擎集中实现，新增成就零代码。
- 称号由成就授予，玩家持有当前称号（后解锁覆盖前）。
- 修为来源 = 任务奖励 + 成就奖励，均为真实数值系统。

### 遇到的问题

- `server.py` 提交失败分支 `events` 未初始化导致 500 → 进入失败分支前初始化 `events = {}`。
- V0.1 测试 `test_playthrough_cultivation_increases` 断言「修为 == 任务奖励总和」被成就奖励打破（first_awaken +10）→ 更新断言为「只增不减且不低于任务奖励总和」。
- E2E 中成就弹窗遮挡突破按钮 → 增加弹窗关闭步骤与 `closeAchievementPopup` 辅助函数；补成就碑与称号校验。
- PowerShell 管道写中文脚本会损坏字符（变 `?`）→ 一律先写 UTF-8 脚本文件再执行，跨脚本传路径用环境变量。

### 测试

- 全量 pytest：142 passed, 16 skipped。
- E2E：24 项检查全部通过（新增：成就碑初始 0/16、首次成就弹窗 first_awaken +10、通关后成就列表与「筑基真人」称号）。

## V0.2 阶段五 · Python 内容扩充（2026-08-08）

### 完成内容

- **境界链扩展至化神**：新增 5 个境界（金丹一层/二层、元婴一层/二层、化神一层），`curriculum.json` order 12-16；`major_realms` 挂接 golden_core / nascent_soul / spirit_transformation。
- **新增 16 个任务**（合计 35）：筑基期「道基巩固」主线修复筑基→金丹断链；五大知识点主线（字符串/异常/模块/文件/OOP）；对应 5 个综合试炼（无参考答案，`no_solution`）；5 个 Debug 挑战（按境界解锁）。
- **沙箱安全升级**：
  - `sandbox_bootstrap.py`：洞府内文件读写守卫（cwd 白名单 + 防穿越），放行标准库导入；`sys.path.insert(0, cwd)` 支持本地模块导入（修复 `-I` 模式下 `ModuleNotFoundError`）。
  - `sandbox.py`：`run_player_code` / `run_validation` 支持 `seed_files`（服务端预置文件，防穿越校验）。
  - `tasks.py`：FUNC_HARNESS 支持 class+method 类方法验证与 raises 预期异常；试炼任务仅当前境界可见（`tasks_trial_available`）。
- **前端**：试炼标签（tag-trial）、`no_solution` 隐藏参考答案按钮、筑基后卡片逻辑（founded+current_task → 修行 / pending → 突破）。
- **成就**：新增 3 项境界成就（金丹/元婴/化神，各 +200/+300/+400 修为）。

### 技术决策

- 综合试炼不设 `solution` 字段：前端隐藏参考答案，AI 师尊 L4 对 `no_solution` 任务返回「回去看教学」话术，杜绝代答。
- 文件/模块类任务通过 seed_files 与洞府内 cwd 白名单实现真实文件读写，验证仍是真实执行，绝无关键词匹配。

### 遇到的问题

- `python -I` 隔离模式不带脚本目录，导致本地模块 import 失败 → 沙箱启动时 `sys.path.insert(0, cwd)`。
- V0.1 旧测试按「已筑基即完结」假设推进 → 适配境界链（筑基后仍可修行/突破金丹），断言改为动态。
- 试炼任务无 solution 导致旧「参考答案可通过」用例误判 → 测试改为内嵌试炼解法并 skip 无解法项。

### 测试

- 新增 `tests/test_v02_content.py` 28 项；全量 pytest **206 passed, 32 skipped**。
- E2E **27 项全部通过**（含筑基→金丹→「净字诀」新流程检查）。

## V0.2 阶段六 · 秘境系统（2026-08-08）

### 完成内容

- **三秘境数据**：`game/data/secret_realms.json`（青云秘境 qi5~筑基 / 万象幻境 金丹~元婴 / 代码天宫 化神以上），各含境界门槛、首通/重复奖励（修为/悟性/道具）、模板池。
- **随机挑战生成器**：`game/secret_realms.py` 9 个模板（三倍数求和/字符串变换/列表统计/函数乘法/异常除法/字符串清洗/字符统计/类方法/模块写入导入），参数随机化产出新任务；产出前用沙箱真实运行参考答案自检，失败则重生成（最多 8 次），保证随机任务可解、可验证。
- **API**：`GET /api/secret-realms`（总览）、`POST /api/secret-realms/<id>/enter`（生成并返回挑战）、`<id>/run`（运行不判定）、`<id>/submit`（验证并结算）；挑战仅存服务端会话，对外 `sanitize` 剔除参考答案与校验结构。
- **解锁与门槛**：秘境引路人（云游子）对话可分别解锁三处秘境（`unlock_secret` 动作）；进入还需境界达标（数据驱动门槛，`is_enterable`）。
- **奖励**：首通（修为+悟性+道具：悟道丹/静心丹/点拨灵符）与重复通关（修为）双轨；`secret_log` 记录历练次数。
- **成就**：新增 4 项（青云初探/万象归真/天宫登临 三秘境首通 + 秘境行者累计 3 次称号）。
- **前端**：洞府地图「秘境入口」卡片、秘境面板（可进入/未解锁/通关次数展示）、任务页复用（秘境标签、运行/提交走秘境 API，师尊指点/诊断可用）。

### 技术决策

- 挑战生成采用「模板 + 参数白名单随机化 + 沙箱自检」策略，从根源消除「随机任务不可解/不可验证」风险。
- 秘境挑战为无参考答案试炼（`no_solution: true`），AI 师尊 L4 不提供答案，符合「引导 > 提示 > 解释 > 答案」铁律。
- 秘境 API 独立于任务 API：挑战不落入课程数据，避免污染主线任务可见性逻辑。

### 遇到的问题

- `_gen_module_summon` 生成器 solution 中 `\n` 双重转义，导致写入秘籍文件的换行变成字面量 `\n`（语法错误）→ 改为单层转义并经沙箱自检 + 全模板回归验证。
- E2E：通关后自动返回洞府，`#task-result` 随 screen-task 隐藏 → 改为以消息弹窗/失败态判定；消息弹窗 DOM 位于成就弹窗之后（顶层遮挡点击）→ 先关消息再关成就弹窗。
- pytest 会话隔离：`server._secret_challenges` 模块级全局未随 app fixture 清理导致用例间串扰 → conftest 补充重置。

### 测试

- 新增 `tests/test_v02_secret.py` 18 项；全量 pytest **224 passed, 32 skipped**。
- E2E **31 项全部通过**（新增秘境面板/进入/通关/状态 4 项）。

## V0.2 阶段七 · 最终验收（2026-08-08）

### 完成内容

- **自动测试**：全量 pytest **224 passed, 32 skipped**（0 failed），V0.1 全部回归通过。
- **E2E 测试**：**31 项全部通过**（新增秘境 4 项：解锁/面板/通关/状态）。
- **完整流程测试**：凡人 → 炼气一~十层 → 筑基天劫 → 筑基 → 道基巩固 → 金丹 → 净字诀；期间完成青云秘境首通。
- **性能/安全/存档检查**：沙箱超时与内存上限；洞府文件白名单与防穿越；多槽位存档 + V0.1 迁移 + 秘境记录持久化。
- **发布**：`python scripts/build.py` 产出 `dist/码上飞升-v0.2.0.pyz`，冒烟验证 **9/9 PASS**（含课程 17 境界与秘境 3 处归档加载检查）。
- **文档**：`docs/V0.2_ACCEPTANCE.md`（七阶段验收清单全 PASS）、`docs/V0.2_TEST_REPORT.md`（测试报告）、`docs/USAGE.md` 与 `ROADMAP.md` 更新至 V0.2。

### 技术决策

- 版本号升级至 0.2.0（`game/__init__.py`），发行包命名随版本。
- 构建冒烟新增秘境数据检查，确保 zipapp 归档内新数据文件正确打包。

### 遇到的问题

- 发行包课程境界数断言仍为 V0.1 的 12 → 更新为 17 并新增秘境断言。
- 多处 V0.1 文案（run.py / bat 标题 / 运行说明）→ 统一升级为 V0.2。

### 测试

- 全量 pytest **224 passed, 32 skipped**；E2E **31 项全部通过**；发行包冒烟 **9/9 PASS**。

## V0.2.5 产品打磨（2026-08-08 夜间优化任务）

### 第一阶段 · 项目审查

- 通读核心文档与 V0.2 全部文档，并用 Playwright 实机走查新玩家/任务/秘境/突破/藏经阁/成就/首页全流程。
- 产出 `docs/NIGHT_REVIEW.md`：当前优势、最大体验问题（新手世界观薄弱、地图首屏溢出、藏经阁超长滚动、成长反馈平淡、成就弹窗遮挡突破）、优化方向。

### 第二阶段 · 新手体验

- **入道启程弹窗**：建角后首次进入弹出（`localStorage("ca_intro_seen")` 防重复），交代「代码即法术」世界观，青玄子传音指引下一步（参悟 `print()` 唤醒灵牌）。
- **下一步引导**：关闭弹窗后洞府修行按钮脉冲高亮（`pulse-cta`）。

### 第三阶段 · 成长反馈

- 任务通过后结果区追加「✦ 奖励入账：修为+X …」（`appendRewardLine`）。
- 修为/悟性/心境/Debug 经验变化时金色闪烁（`flashAttrChanges` + `flash-gold`）。
- 突破弹窗新增「新境感悟 + 新参悟功法」详情行（`renderBreakthroughDetail`，功法名用 `t.title`）。

### 第四阶段 · UI 体验

- 地图卡片紧凑化：1280×800 实测全部入口首屏可见，折叠线以下仅剩 NPC 带。
- 藏经阁功法讲解默认折叠，点击展开，消除 1415px 超长滚动。

### 第五阶段 · 稳定性测试

- 新增 `tests/test_v02_5_stability.py` **15 项**：存档（损坏→None / 路径穿越清洗 / V0.1 迁移 / 字段往返）、API 边界（空代码、无 body、未知道具 400、未知任务 404）、心境钳制（连败→0、成功恢复 + streak、attempts 只增不减）、秘境边界（超境界 403、未知秘境 run 400）、沙箱补充（空代码、相对路径穿越拦截）。

### 第六阶段 · 代码质量

- 清理 `static/js/app.js` 死代码 `realmName()`；`game/` 全模块无未使用导入；前端 `node --check` 通过。
- E2E 适配：建角后新增「关闭入道弹窗」步骤，避免弹窗拦截地图卡片点击。

### 测试

- 全量 pytest **239 passed, 32 skipped**（基线 224 + 新增 15，0 failed）。
- E2E **31 项全部通过**；发行构建冒烟 **9/9 PASS**，产物 `dist/码上飞升-v0.2.5.pyz`。
- 文档：`docs/NIGHT_REVIEW.md`、`docs/V0.2.5_REPORT.md`。

### 技术决策

- 版本号 0.2.0 → 0.2.5，发行包与启动文案同步。
- 坚持小步优化：未改动沙箱核心验证、未改动数据驱动架构、未删任何已有功能。

### 遇到的问题

- E2E 因新增入道弹窗全屏遮挡而点击超时 → 建角后显式关闭弹窗（`closeIntroModal`）。
- PowerShell 管道写中文文件损坏 → 统一以 UTF-8 无 BOM 输出编码写盘。

## V0.3 产品设计阶段（2026-08-08）

### 完成内容

- **体验审查**：实机走查 V0.2.5 新玩家全流程（Playwright，1280×900，截图 `.tools/v03_shots/`），输出 `docs/V0.3_REVIEW.md`。
  - 核心结论：玩家目前更接近「在做 Python 练习，界面是修仙风」，而非「生活在修仙世界」；差距在空间/人物/事件/选择四层。
- **产品设计**：输出 `docs/V0.3_DESIGN.md`（九章）：
  - 世界地图：青云宗 / 青云城 / 后山秘境 3 区域 12+ 地点，「区域-节点」二维地图（非 3D），连通关系与解锁条件数据化。
  - NPC：青玄子 / 云游子 / 玄机长老 / 掌门 四位核心 NPC（背景/性格/对话风格/任务关系/成长路线），好感度与在场系统。
  - 功法：首批 12 门功法独立数据化，4 级熟练度（入门→圆满），演武场修炼/考核全部真实代码验证，功法树。
  - 剧情：主线章节制（炼气篇「宗门危机」为核心）、任务堂支线、≥8 种随机奇遇、境界剧情覆盖每次突破。
  - 长期成长：六大留存动机（境界/功法/探索/剧情/关系/收集），禁止纯数值挂机。
  - 技术方案：新增 `world.json` / `story.json` / `techniques.json`，扩展 npcs/dialogues/tasks，Player 新增 7 字段（默认值兼容旧档），save version 2→3；**无需架构级重构**，沙箱/验证核心零改动。
  - 开发顺序 A~F（地图→NPC→功法→剧情→成长闭环→测试发布），风险分析 7 项。

### 技术决策

- V0.3 采用「区域-地点」节点图而非自由行走，最大化兼容现有卡片架构，控制开发复杂度。
- 所有新成长系统绑定真实代码验证，延续「禁止挂机」产品红线。

### 下一步

- 等待 V0.3 开发阶段指令（阶段 A：世界地图实现）。

## GitHub 开源发布（2026-08-08）

- 创建公开仓库 [Hinln/CodeDaoLab](https://github.com/Hinln/CodeDaoLab)（PUBLIC，`main` 分支）。
- 新增开源文档：`README.md`（项目介绍/核心功能/技术架构/部署教程/测试）、`LICENSE`（Apache-2.0，Copyright 2026 Hinln）、`NOTICE`、`CONTRIBUTING.md`（Issue/PR/代码/文档规范）、`CHANGELOG.md`（V0.1/V0.2/V0.2.5）。
- 安全整理：剔除 `提示词/` 目录并加入 `.gitignore`（任务提示词不随仓库公开）；复查确认无密钥/Token/存档/构建产物/缓存/IDE 配置。
- 部署实测：全新 venv 按 README 流程 `pip install -r requirements.txt` + `python run.py` 启动成功（首页与 API 均 200）。
- 提交：`feat: initial release of CodeDaoLab`（单一初始提交，78 文件）。
- 报告：`docs/GITHUB_RELEASE_REPORT.md`。

## 下一步计划（V0.3 起）

- V0.3 展望：炼虚/合体/大乘/渡劫境界链补全、更多随机秘境模板与奖励、对话树扩展、跨平台打包、CI（pytest + E2E）自动化接入、账号与云存档评估。
