#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""《码上飞升》启动入口。

用法：
    python run.py                 # 启动服务器并自动打开浏览器
    python run.py --no-browser    # 仅启动服务器
    python run.py --port 9000     # 自定义端口
"""

from __future__ import annotations

import argparse
import threading
import webbrowser

from game import config
from game.server import run


def main() -> None:
    parser = argparse.ArgumentParser(description="码上飞升 V0.2.5")
    parser.add_argument("--host", default=config.HOST, help="监听地址")
    parser.add_argument("--port", type=int, default=config.PORT, help="监听端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    url = "http://%s:%d/" % (args.host, args.port)
    print("=" * 44)
    print("《码上飞升》V0.2.5 已启动")
    print("大道三千，代码亦可入道。")
    print("请访问：%s" % url)
    print("按 Ctrl+C 退出游戏服务")
    print("=" * 44)

    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
