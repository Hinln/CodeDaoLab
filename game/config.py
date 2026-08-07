# -*- coding: utf-8 -*-
"""全局配置常量。

同时支持两种运行形态：
- 源码运行（仓库目录内）：static/ 直接使用磁盘目录，saves/ 位于项目根目录；
- zipapp 打包运行（dist/*.pyz）：static 与课程数据从归档内读取，
  存档写入用户数据目录（可用环境变量 CA_SAVE_DIR 覆盖）。
"""

from __future__ import annotations

import os

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 是否运行在 zipapp 打包模式（__file__ 形如 .../xxx.pyz/game/config.py）
_ZIP_MARK = ".pyz" + os.sep
_THIS_FILE = os.path.abspath(__file__)
ZIP_MODE = _ZIP_MARK in _THIS_FILE and not os.path.isdir(
    os.path.join(ROOT_DIR, "static")
)
ZIP_ARCHIVE = _THIS_FILE.split(_ZIP_MARK, 1)[0] + ".pyz" if ZIP_MODE else None

# 静态资源目录（源码模式）
STATIC_DIR = os.path.join(ROOT_DIR, "static")

# 存档目录：优先使用环境变量覆盖（测试/打包验证使用）
_env_save = os.environ.get("CA_SAVE_DIR")
if _env_save:
    SAVE_DIR = os.path.abspath(_env_save)
elif ZIP_MODE:
    # 打包模式下存档放在用户数据目录，避免写入不可写的安装目录
    _local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.code_ascension")
    SAVE_DIR = os.path.join(_local, "CodeAscension", "saves")
else:
    SAVE_DIR = os.path.join(ROOT_DIR, "saves")

# 默认存档槽位
DEFAULT_SLOT = "default"

# 服务器配置
HOST = "127.0.0.1"
PORT = 8756

# 沙箱默认限制
DEFAULT_TIME_LIMIT = 5.0        # 秒
DEFAULT_MEMORY_LIMIT_MB = 256   # MB
MAX_OUTPUT_CHARS = 65536        # 输出字符上限
