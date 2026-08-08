# CodeDaoLab Godot Edition V0.2.0 发布说明

## 发布物

- 文件：`CodeDaoLab-Qingyun-Demo-v0.2.0.zip`
- 大小：82.3 MB
- 平台：Windows 10/11
- Godot：4.7.1 stable official，运行时已包含
- Python：需要 Python 3.10+

## 启动

1. 解压 ZIP 到普通可写目录。
2. 双击 `Start-Qingyun-Demo.bat`。
3. 创建道号、灵根和身份，循任务卡与世界灵光进入青云宗。

操作：`WASD` 或方向键移动，`E` 交互。

## V0.2.0 重点内容

- 代码从输入到结果的完整施法表现。
- 四类错误反噬和 Python 环境异常区分。
- 当前目标、地点距离、世界灵光和青玄子传音。
- 五灵根、三身份与个性化突破色彩。
- 三名 NPC 立绘、表情、记忆和关系阶段。
- 五地点天气、灵息、程序化环境音和观察点。
- 三门功法的入门、运转、小成成长路径。
- 语法、逻辑、变量三阶段 Bug 妖战斗。
- 结构化导师历史、成功复盘和离线规则兜底。
- 展示角色、功法、关系与师尊评语的章节结算。

## 数据与隐私

- Godot Edition 使用独立 `user://` 存档。
- 师尊记忆只保存挑战结果和提示使用等结构化状态，不保存玩家源码。
- 玩家代码由随包 Python 桥接在独立沙箱进程中执行。

## 源码命令

```powershell
godot\scripts\run_tests.ps1
godot\scripts\build_release.ps1
```

构建脚本会运行 181 项 Godot 检查、导出 PCK、组装官方 Godot 运行时、验证发布目录 Python 判题、执行发布版启动冒烟并生成 ZIP。

## 已知限制

- 未内嵌 Python 解释器，未安装 Python 3.10+ 的设备无法完成代码试炼。
- 第一章内容按 25-35 分钟设计，实际时长会随 Python 经验不同而变化。
- 当前版本聚焦第一章体验，不包含 Web Edition 的全部长期境界内容。
