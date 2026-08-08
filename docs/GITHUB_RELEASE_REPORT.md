# CodeDaoLab GitHub 开源发布报告

> 发布时间：2026-08-08。仓库：[https://github.com/Hinln/CodeDaoLab](https://github.com/Hinln/CodeDaoLab)（PUBLIC，默认分支 `main`）。

## 1. 发布内容

- 项目：《码上飞升》（CodeDaoLab）V0.2.5（当前稳定版本），V0.3 处于产品设计阶段（`docs/V0.3_DESIGN.md`）。
- 定位：东方修仙世界观下的 Python 编程学习 RPG；代码是力量体系，学习即修炼。
- 技术栈：Python 3.10+ / Flask / 原生 JS + CodeMirror 5（本地资源，无 CDN）/ JSON 数据驱动。

## 2. 仓库文件清单（78 个）

| 类别 | 文件 |
| --- | --- |
| 发布文档 | `README.md`、`LICENSE`（Apache-2.0）、`NOTICE`、`CONTRIBUTING.md`、`CHANGELOG.md` |
| 项目文档 | `CODEX.md`、`PRODUCT.md`、`GAME_DESIGN.md`、`PYTHON_CURRICULUM.md`、`TECH_ARCHITECTURE.md`、`ACCEPTANCE_CRITERIA.md`、`WORLD.md`、`ROADMAP.md`、`DEVLOG.md` |
| 设计文档 | `docs/`（V0.1~V0.3 设计、验收、测试报告、审查报告） |
| 后端源码 | `game/`（server / sandbox / player / save / tasks / curriculum / npcs / dialogues / techniques / secret_realms / achievements / items / ai / data JSON） |
| 前端 | `static/`（index.html / css / js / vendor CodeMirror） |
| 测试 | `tests/`（pytest 239 项）、`scripts/e2e_test.js`（E2E 31 项）、`scripts/build.py`（发行构建） |
| 入口 | `run.py`、`requirements.txt`（flask>=3.0、pytest>=8.0）、`.gitignore` |

## 3. 提交记录

- `feat: initial release of CodeDaoLab`（单一初始提交，78 个文件；具体哈希见仓库提交记录）。

## 4. 安全与隐私检查

- 已从仓库剔除：`提示词/`（用户提供的任务提示词，**不推送**）并加入 `.gitignore`。
- `.gitignore` 覆盖：`saves/`（存档）、`dist/`（构建产物）、`.tools/`（本地工具/截图/测试存档）、`__pycache__/`、`.pytest_cache/`、`.env`、`*.log`、IDE 配置（`.vscode/`、`.idea/`）。
- 全仓扫描确认：无 API Key / Token / 私钥硬编码（AI 接口仅引用环境变量 `CA_AI_API_KEY` 等，无真实值）。

## 5. 部署测试（按 README 教程实测）

- 环境：全新 `python -m venv`（Python 3.13.14）→ `pip install -r requirements.txt`（成功，flask 3.1.3）。
- `python run.py --no-browser --port 8899`：`/api/state` 200、首页 `/` 200，启动正常。
- 结论：README「本地部署 / Windows 部署 / Linux 部署」流程真实可复现；Docker 已如实注明未提供 Dockerfile。

## 6. 已知问题

- README 中 AI 师尊的 OpenAI 兼容接入需要外部模型服务，未配置时自动使用本地引擎（无需任何外部依赖）。
- 沙箱执行依赖宿主 Python 解释器，发行包（zipapp）不兼容 PyInstaller 等冻结打包器（已在 `scripts/build.py` 注明）。
- E2E 测试需要 Node.js 与系统 Chrome（仅测试需要，运行游戏不需要）。

## 7. 后续建议

- 为仓库补充 GitHub Topics（python / game / education / rpg / flask）与仓库描述。
- 接入 CI（GitHub Actions：pytest + E2E），在 README 添加状态徽章。
- V0.3 开发完成后更新 CHANGELOG 与 README 功能清单。
