# 《码上飞升》V0.1 验收清单

> 对照 `ACCEPTANCE_CRITERIA.md` 逐条验收。状态：PASS = 已实现并通过实际测试。
> 证据格式：【测试】= pytest 用例；【E2E】= scripts/e2e_test.js 检查项；【构建】= scripts/build.py 冒烟验证。

## 游戏基础

- [x] **可以启动游戏**
  - 【构建】发行包冒烟验证第 1 项“首页渲染”；`python run.py` 与 `dist/启动游戏.bat` 实测可启动。
- [x] **可以创建角色**
  - 【测试】`tests/test_api.py::test_new_game`（建号返回境界=凡人、初始任务=唤醒灵牌）
  - 【E2E】“创建角色 → 进入洞府地图”
- [x] **可以进入世界**
  - 【E2E】“创建角色 → 进入洞府地图”（洞府地图含洞府修行/炼丹房/渡劫台三张卡片）
- [x] **可以完成新手剧情**
  - 【测试】`tests/test_api.py::test_submit_wrong_then_right`（提交正确代码后 `pending_breakthrough=True`）
  - 【E2E】“正确提交 → 突破至炼气一层”（凡人任务“唤醒灵牌”剧情 + 突破弹窗）
- [x] **可以保存和读取存档**
  - 【测试】`tests/test_api.py::test_save_and_load`（模拟重启后从存档恢复至炼气一层）
  - 【E2E】“存档续玩（qi10 状态保持）”“存档续玩：境界=筑基”

## Python 系统

- [x] **内置代码编辑器**
  - 【E2E】任务界面使用 CodeMirror 编辑器（“任务屏幕”“运行”等检查项）；`static/vendor/codemirror.min.js` 随包发布。
- [x] **可以运行 Python 代码**
  - 【测试】`tests/test_sandbox.py` 27 项；`tests/test_api.py::test_run_endpoint`
  - 【构建】冒烟验证第 6 项“沙箱真实执行”
- [x] **正确显示输出**
  - 【测试】沙箱输出解析与 `normalize_output` 精确比对用例
  - 【E2E】“运行玩家代码并显示输出”
- [x] **正确处理语法错误**
  - 【测试】`tests/test_sandbox.py` 语法错误用例（返回中文摘要与错误行号）
- [x] **正确处理运行错误**
  - 【测试】`tests/test_sandbox.py` 运行错误用例（异常类型 + traceback 片段）
- [x] **防止无限循环**
  - 【测试】`tests/test_sandbox.py` 超时用例（5 秒超时强杀 + “心魔入体”提示）
- [x] **Python 环境安全隔离**
  - 【测试】沙箱隔离用例：`-I` 隔离子进程、危险模块/内建屏蔽、`open` 白名单、内存上限（256 MB）、临时 cwd、最小环境变量。

## 炼气期内容

- [x] **Hello World 任务**
  - 【测试】`test_solution_passes[hello_world]`、`test_output_task_rejects_wrong_output`
  - 任务：`qi1/hello_world`「第一道真言」
- [x] **变量任务**
  - 【测试】`test_solution_passes[variable_intro]`
  - 任务：`qi2/variable_intro`「灵力容器」
- [x] **条件判断任务**
  - 【测试】`test_solution_passes[conditionals]`、`test_function_task_rejects_wrong_logic`
  - 任务：`qi6/conditionals`「道心抉择」（函数用例验证）
- [x] **循环任务**
  - 【测试】`test_solution_passes[for_loop]`、`test_solution_passes[while_loop]`
  - 任务：`qi7/for_loop`「周天搬运」、`qi8/while_loop`「不息之泉」
- [x] **函数任务**
  - 【测试】`test_solution_passes[functions]`、`test_function_task_rejects_wrong_name`
  - 任务：`qi10/functions`「功法真意」
- [x] **Debug 任务**
  - 【测试】`test_buggy_starter_fails[debug_*]`（心魔初始代码必须失败）+ `test_solution_passes[debug_*]`
  - 【E2E】“炼丹房 Debug 任务界面”
  - 任务：`debug_1` 缩进之乱、`debug_2` 永夜之环、`debug_3` 真假倒错、`debug_4` 有去无回

## 发布

- [x] **Release 构建成功**
  - 【构建】`python scripts/build.py` 产出 `dist/码上飞升-v0.1.0.pyz` 并 8/8 冒烟验证通过；`启动游戏.bat` 实测可运行。
- [x] **使用说明完成**
  - 【文档】`docs/USAGE.md`（运行/构建/存档/常见问题）、`dist/运行说明.txt`
- [x] **无重大 Bug**
  - 【测试】89 passed + E2E 全通过 + 构建冒烟全通过；已知限制见 `docs/TEST_REPORT.md` 第 6 节，均非阻断性缺陷。

## 结论

V0.1 全部验收项 **PASS**。玩家可完整体验：凡人 → 学习 Python（12 境界教学）→ 11 个主线任务 → 4 个 Debug → 3 道筑基天劫 → 筑基成功，且全过程为真实代码执行验证。
