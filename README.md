# CodeDaoLab（码上飞升）

> 大道三千，代码亦可入道。

CodeDaoLab 是一款**东方修仙世界观下的 Python 编程学习 RPG**。在这个世界里，**代码即法术**：变量是灵力容器，函数是功法，Bug 是心魔，Debug 是破境，项目是历练。玩家通过真实编写并运行 Python 代码，推动剧情、完成任务、闯荡秘境、突破境界，最终飞升。

学习不是游戏的附属玩法——**Python 是这个世界的力量体系**。境界提升必须通过真实代码验证，不提供挂机或伪判定。

---

## 核心功能

- **修仙成长**：凡人 → 炼气（一~十层）→ 筑基 → 金丹 → 元婴 → 化神，共 17 个境界；每次突破都必须通过代码验证；渡劫台阶段大考，筑基天劫等剧情节点。
- **Python 学习**：知识以「功法」形式呈现（教学 + 心法口诀），覆盖变量、数据类型、条件分支、循环、函数、字符串、列表、字典、异常处理、模块、文件读写、面向对象（OOP）。
- **任务系统**：主线任务 / 炼丹房 Debug / 支线机缘 / 综合试炼 / 秘境挑战；全部由**真实代码运行结果**判定，无关键词匹配。
- **秘境挑战**：随机生成的代码挑战（模板 + 参数随机化 + 沙箱自检保证可解），包含青云秘境 / 万象幻境 / 代码天宫，按境界门槛解锁。
- **Debug 系统（炼丹房）**：修复含 Bug 的代码（心魔），破除心魔获得 Debug 经验。
- **AI 师尊**：分级引导（方向 → 提示 → 解释 → 答案），自动诊断语法 / 运行 / 超时 / 内存错误；本地引擎开箱即用，可选接入 OpenAI 兼容 API（环境变量 `CA_AI_BASE_URL` / `CA_AI_API_KEY` / `CA_AI_MODEL`）。
- **沙箱执行**：玩家代码在隔离子进程中真实执行（`python -I`），带超时控制、内存上限、文件白名单与危险模块拦截，防止无限循环与越权访问。
- **成长与收集**：悟性 / 心境 / Debug 经验属性，功法藏经阁，成就碑，道具储物袋，多 NPC 节点式对话，多槽位 JSON 存档（自动兼容旧版本存档）。

> V0.3 规划（设计中，尚未实现）：可探索的世界地图、NPC 好感度、主线章节剧情、随机奇遇、功法熟练度与修炼系统。详见 `docs/V0.3_DESIGN.md`。

---

## 技术架构

| 层 | 技术方案 |
| --- | --- |
| 后端 | Python 3.10+ / Flask（REST API + 静态资源托管） |
| 前端 | 原生 JavaScript + CodeMirror 5 代码编辑器（本地 vendor 资源，无 CDN 依赖，可离线运行） |
| 数据 | JSON 数据驱动：课程 / 任务 / NPC / 对话 / 功法 / 秘境 / 成就 / 道具 |
| 沙箱 | 隔离子进程 `python -I -E -u -X utf8`；Windows Job Object 内存限制、POSIX setrlimit；超时控制；`open` 等文件操作白名单守卫 |
| AI 师尊 | 本地规则引擎（默认，无外部依赖）+ OpenAI 兼容接口（可选） |
| 测试 | pytest（后端单元 / 集成，239 项）+ playwright-core E2E（前端全流程，31 项）+ 发行构建冒烟（9/9） |

---

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- （可选）Node.js 与 Chrome：仅运行 E2E 测试时需要
- 无其他外部服务依赖（AI 师尊本地引擎开箱即用）

### 本地部署（通用）

```bash
git clone https://github.com/Hinln/CodeDaoLab.git
cd CodeDaoLab
pip install -r requirements.txt
python run.py
```

启动后浏览器自动打开 `http://127.0.0.1:8756`；如需指定端口：

```bash
python run.py --port 9000 --no-browser
```

### Windows 部署

1. 安装 [Python 3.10+](https://www.python.org/downloads/)，安装时勾选 **Add Python to PATH**。
2. 打开 PowerShell 或 CMD，进入项目目录。
3. 安装依赖并启动：

```powershell
pip install -r requirements.txt
python run.py
```

4. 如需发行单文件包：`python scripts/build.py`，产物在 `dist/` 目录（`码上飞升-vX.Y.Z.pyz` + `启动游戏.bat`，双击即运行）。

### Linux 部署

以 Ubuntu/Debian 为例：

```bash
sudo apt update
sudo apt install -y python3 python3-pip
cd CodeDaoLab
pip3 install -r requirements.txt
python3 run.py --no-browser
```

后台运行：

```bash
nohup python3 run.py --host 0.0.0.0 --port 8756 --no-browser > game.log 2>&1 &
```

### Docker

当前版本**未提供 Dockerfile**。项目仅依赖系统 Python 与 Flask，直接以系统级部署即可（见上方 Linux 部署）；如需容器化，可基于 `python:3.13-slim` 自行构建镜像后运行 `python run.py`。

---

## 测试

```bash
# 后端单元 / 集成测试
python -m pytest -q

# 前端端到端测试（需 Node.js + Chrome，自动使用隔离存档目录）
node scripts/e2e_test.js

# 发行构建 + 启动冒烟验证
python scripts/build.py
```

---

## 目录结构

```
├── game/                 # 后端源码
│   ├── data/             # JSON 数据（课程/任务/NPC/对话/秘境/成就/道具）
│   ├── ai/               # AI 师尊（本地引擎 + OpenAI 兼容）
│   ├── sandbox.py        # 玩家代码沙箱执行
│   ├── server.py         # Flask API 与静态托管
│   └── ...               # 玩家/存档/任务/课程/NPC/对话/功法/秘境/成就/道具
├── static/               # 前端（index.html / css / js / vendor CodeMirror）
├── scripts/              # E2E 测试、发行构建、开发脚本
├── tests/                # pytest 测试（239 项）
├── docs/                 # 设计文档与测试报告
├── run.py                # 启动入口
└── requirements.txt      # Python 依赖（flask / pytest）
```

---

## 文档索引

| 文档 | 说明 |
| --- | --- |
| `PRODUCT.md` | 产品总纲与核心理念 |
| `GAME_DESIGN.md` | 游戏设计 |
| `PYTHON_CURRICULUM.md` | Python 课程体系 |
| `TECH_ARCHITECTURE.md` | 技术架构要求 |
| `ACCEPTANCE_CRITERIA.md` | 验收标准 |
| `docs/V0.3_DESIGN.md` | V0.3 世界展开阶段设计 |
| `CHANGELOG.md` | 版本更新日志 |

---

## 开源协议

本项目基于 **Apache License 2.0** 开源，详见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。

Copyright 2026 Hinln
