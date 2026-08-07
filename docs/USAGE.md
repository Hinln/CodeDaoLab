# 《码上飞升》V0.2 使用说明

## 1. 环境要求

- Python 3.10 或更高版本（开发环境为 Python 3.13）
- 运行游戏需安装 Flask：`pip install flask`
- 运行测试需安装 pytest：`pip install pytest`
- 运行 E2E 需 Node.js 与系统 Chrome（可选）

安装依赖：

```bash
pip install -r requirements.txt
```

## 2. 源码运行

在项目根目录执行：

```bash
python run.py
```

启动后自动打开浏览器，默认地址 `http://127.0.0.1:8756`。

常用参数：

```bash
python run.py --no-browser        # 不自动打开浏览器
python run.py --port 9000         # 自定义端口
python run.py --host 0.0.0.0      # 允许局域网访问
```

按 `Ctrl+C` 停止服务。

## 3. Release 构建

```bash
python scripts/build.py            # 构建 + 发行包冒烟验证
python scripts/build.py --no-verify  # 仅构建，跳过验证
```

产物输出到 `dist/`：

| 文件 | 说明 |
| --- | --- |
| `码上飞升-v0.2.0.pyz` | 单文件可运行包（zipapp） |
| `启动游戏.bat` | Windows 一键启动脚本 |
| `运行说明.txt` | 简版说明 |

## 4. 运行 Release 包

Windows：双击 `dist/启动游戏.bat`；或命令行：

```bash
python dist/码上飞升-v0.2.0.pyz
```

发行包要求目标机器已安装 Python 与 Flask（见第 1 节）。

## 5. 存档位置

| 运行方式 | 存档目录 |
| --- | --- |
| 源码运行 | `<项目根>/saves/` |
| zipapp 发行包 | Windows：`%LOCALAPPDATA%\CodeAscension\saves`；其他：`~/.code_ascension/saves` |

可通过环境变量 `CA_SAVE_DIR` 覆盖存档目录（测试/验证使用）。

## 6. 测试

```bash
# 单元与集成测试（沙箱、任务、API、完整通关）
python -m pytest tests -q

# 端到端测试（需系统 Chrome，node 24+）
node scripts/e2e_test.js
```

## 7. 游戏操作

- 标题页：开始修行 / 继续修行（有存档时）。
- 建角页：输入道号、选择灵根，确认入道。
- 洞府地图：洞府修行（主线任务）、炼丹房（Debug）、渡劫台（天劫）、藏经阁（功法）、秘境入口（随机挑战）、机缘簿（支线）、储物袋、成就碑。
- 秘境：与「秘境引路人（云游子）」对话解锁，境界达标后可从秘境入口进入随机挑战，通关获得修为/悟性/道具奖励。
- AI 师尊：任务页点击「求指点」按 L1→L4 分级提示；「请诊断」真实运行代码并归因错误。
- 任务页：左侧剧情与功法讲解，右侧 CodeMirror 编辑器；「运行」查看输出，「提交验证」判定是否通过。
- 突破：境界任务全部完成后，洞府卡片变为「运功突破」。
- 渡劫台：炼气大圆满后开启，依次渡过心魔劫、九霄神雷劫、道心劫即可筑基。

## 8. 常见问题

| 问题 | 处理 |
| --- | --- |
| 提示未找到 Python | 安装 Python 并勾选 “Add Python to PATH” |
| `ModuleNotFoundError: flask` | 执行 `pip install flask` |
| 浏览器未自动打开 | 加 `--no-browser` 手动访问 `http://127.0.0.1:8756` |
| 端口被占用 | `python run.py --port 9000` |
| 代码运行超时 | 任务自带 5 秒限制，用于拦截无限循环，属正常保护 |
