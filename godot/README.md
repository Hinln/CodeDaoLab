# 《码上飞升：青云宗篇》Godot Edition

独立 Godot 4.x 子项目。Web Edition 位于仓库根目录，两者不共享运行时存档。

## 开发运行

```powershell
Godot_v4.7.1-stable_win64_console.exe --editor --path godot
```

无头启动检查：

```powershell
Godot_v4.7.1-stable_win64_console.exe --headless --path godot --quit-after 3
```

## 当前目标

完成《青云宗篇》第一章：创建角色、探索青云宗、拜见青玄子、学习功法、完成真实 Python 代码试炼、击败 Bug 妖并突破炼气境。

当前阶段使用程序化占位资源，玩法闭环通过后再按 `ART_STYLE_GUIDE.md` 替换关键美术。

## 已完成的 Demo 流程

创建角色 → 进入青云宗 → 探索五处地点 → 拜见青玄子 → 学习真言诀/变量吐纳诀/循环周天诀 → 完成真实 Python 试炼 → 三阶段击败 Bug 妖 → 突破炼气一层。

## 自动测试

```powershell
powershell -ExecutionPolicy Bypass -File godot/scripts/run_tests.ps1
```

## Windows 便携发布

```powershell
powershell -ExecutionPolicy Bypass -File godot/scripts/build_release.ps1
```

发布包使用官方 Godot 标准运行程序 + PCK，包含外置 Python 桥和隔离沙箱运行时。目标机器需要 Python 3.10+，无需安装 Godot；双击 `Start-Qingyun-Demo.bat` 启动。
