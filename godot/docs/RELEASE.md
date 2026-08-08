# CodeDaoLab Godot Edition V0.1.0 发布说明

## 发布物

- 文件：`CodeDaoLab-Qingyun-Demo-v0.1.0.zip`
- 大小：82.3 MB
- 平台：Windows 10/11
- Godot：4.7.1 stable official，运行时已包含
- Python：需要 Python 3.10+

## 启动方式

1. 解压 ZIP 到普通可写目录。
2. 双击 `Start-Qingyun-Demo.bat`。
3. 在标题界面选择新游戏并创建角色。

移动使用 `WASD` 或方向键，交互使用 `E`。代码试炼会调用系统中的 `python` 命令，并通过独立沙箱进程执行。

## 本版内容

- 青云门 2.5D 可探索场景与五处功能地点。
- 三名剧情 NPC、任务链和关系变化。
- 真言诀、变量吐纳诀、循环周天诀三门术法。
- 基于真实 Python 的代码修炼与三阶段 Bug 妖战斗。
- L1-L4 自适应导师提示。
- 引气入体、炼气一层和第一章结算。
- 独立存档与继续游戏。

## 源码构建

在仓库根目录执行：

```powershell
godot\scripts\run_tests.ps1
godot\scripts\build_release.ps1
```

`build_release.ps1` 会执行 Godot 测试、导出 PCK、组装运行时、验证 Python 桥接、启动发布版冒烟测试并生成 ZIP。脚本使用仓库内 `.tools/godot` 的官方便携版 Godot。

## 已知限制

- 未随包嵌入 Python 解释器，未安装 Python 的设备无法完成代码试炼。
- 本包是第一章演示，不等同于 Web Edition 的全部长期养成内容。
- 使用官方标准 Godot 运行时，包体优先保证稳定与可复现，而非最小体积。
