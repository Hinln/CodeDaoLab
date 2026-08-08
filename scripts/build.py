#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""《码上飞升》V0.3.0 Release 构建脚本。

产物（输出到 dist/）：
    码上飞升-vX.Y.Z.pyz   单文件可运行包（zipapp）
    启动游戏.bat          Windows 一键启动脚本
    运行说明.txt          简要使用说明

用法：
    python scripts/build.py              # 构建并执行启动冒烟验证
    python scripts/build.py --no-verify  # 仅构建，不验证

说明：
    发行包要求目标机器安装 Python 3.10+ 与 Flask（pip install flask）。
    玩家代码沙箱复用宿主 Python 解释器（sys.executable），因此发行包必须由
    真实 Python 运行，不能与 PyInstaller 等冻结打包器混用。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STAGING = DIST / "_staging"

_MAIN_TEMPLATE = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""码上飞升 发行包入口。"""

from run import main

if __name__ == "__main__":
    main()
'''


def _version() -> str:
    text = (ROOT / "game" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else "0.1.0"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _copy_tree(src: Path, dst: Path) -> None:
    """复制目录树，排除 __pycache__ 与编译产物。"""
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if any(part == "__pycache__" for part in rel.parts):
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.suffix not in (".pyc", ".pyo"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _make_staging() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)
    (STAGING / "__main__.py").write_text(_MAIN_TEMPLATE, encoding="utf-8")
    shutil.copy2(ROOT / "run.py", STAGING / "run.py")
    _copy_tree(ROOT / "game", STAGING / "game")
    _copy_tree(ROOT / "static", STAGING / "static")


def _write_launcher(archive_name: str) -> None:
    bat = DIST / "启动游戏.bat"
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "title 码上飞升 V0.3.0",
        'cd /d "%~dp0"',
        "where python >nul 2>nul",
        "if errorlevel 1 (",
        "  echo [错误] 未找到 Python，请先安装 Python 3.10+ 并勾选“Add Python to PATH”。",
        "  pause",
        "  exit /b 1",
        ")",
        f'python "%~dp0{archive_name}" %*',
        "pause",
        "",
    ]
    bat.write_text("\r\n".join(lines), encoding="utf-8")


def _write_readme(archive_name: str) -> None:
    txt = DIST / "运行说明.txt"
    content = f"""《码上飞升》V0.3.0 Release 包
=============================

【运行方式】
  1. 双击「启动游戏.bat」即可启动游戏，浏览器会自动打开。
     或在命令行执行：python {archive_name}

【环境要求】
  - Python 3.10 或更高版本
  - 首次运行前安装依赖：pip install flask

【存档位置】
  Windows：%LOCALAPPDATA%\\CodeAscension\\saves
  其他系统：~/.code_ascension/saves

【常见问题】
  - 提示“未找到 Python”：请安装 Python 并勾选 “Add Python to PATH”。
  - 提示“ModuleNotFoundError: flask”：先执行 pip install flask。
  - 无法打开浏览器：命令行加 --no-browser 手动访问 http://127.0.0.1:8756

【更多说明】见项目 docs/USAGE.md
"""
    txt.write_text(content, encoding="utf-8")


def build() -> Path:
    """构建 zipapp 与 Windows 启动脚本，返回归档路径。"""
    DIST.mkdir(exist_ok=True)
    _make_staging()
    archive_name = f"码上飞升-v{_version()}.pyz"
    target = DIST / archive_name
    if target.exists():
        target.unlink()
    zipapp.create_archive(str(STAGING), str(target), compressed=True)
    _write_launcher(archive_name)
    _write_readme(archive_name)
    return target


def _http(method: str, url: str, body: dict | None = None, timeout: float = 30) -> tuple[int, str]:
    req = urllib.request.Request(url, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")


def verify(archive: Path) -> bool:
    """对发行包做启动冒烟验证：静态资源、API、沙箱、提交、课程数据。"""
    port = _free_port()
    env = dict(os.environ)
    env["CA_SAVE_DIR"] = str(Path(tempfile.mkdtemp(prefix="ca_build_verify_")) / "saves")

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        [sys.executable, str(archive), "--no-browser", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    base = "http://127.0.0.1:%d" % port
    checks: list[tuple[str, bool]] = []
    try:
        ready = False
        for _ in range(80):
            if proc.poll() is not None:
                break
            try:
                st, _ = _http("GET", base + "/api/state", timeout=2)
                if st == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.25)
        if not ready:
            out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
            raise RuntimeError("发行包服务器未就绪。\n" + out)

        st, html = _http("GET", base + "/")
        checks.append(("首页渲染", st == 200 and "码上飞升" in html))
        st, js = _http("GET", base + "/static/js/app.js")
        checks.append(("静态资源服务", st == 200 and "App" in js))
        st, css = _http("GET", base + "/static/vendor/codemirror.min.js")
        checks.append(("编辑器资源服务", st == 200 and "CodeMirror" in css))
        st, state = _http("GET", base + "/api/state")
        checks.append(("无存档初始状态", st == 200 and json.loads(state).get("player") is None))
        st, _ = _http("POST", base + "/api/game/new", {"name": "构建验证", "spirit_root": "金"})
        checks.append(("创建角色", st == 200))
        st, body = _http(
            "POST",
            base + "/api/tasks/tutorial_run/run",
            {"code": "print('天地玄黄，宇宙洪荒。')"},
        )
        run = json.loads(body).get("run", {})
        checks.append(("沙箱真实执行", st == 200 and run.get("status") == "ok" and "天地玄黄" in run.get("stdout", "")))
        st, body = _http(
            "POST",
            base + "/api/tasks/tutorial_run/submit",
            {"code": "print('天地玄黄，宇宙洪荒。')"},
        )
        checks.append(("提交验证通过", st == 200 and json.loads(body)["outcome"]["passed"] is True))
        st, body = _http("GET", base + "/api/curriculum")
        cur = json.loads(body)
        checks.append(("课程数据从归档加载", st == 200 and len(cur.get("realms", [])) == 17))
        st, body = _http("GET", base + "/api/secret-realms")
        sec = json.loads(body)
        checks.append(("秘境数据从归档加载", st == 200 and len(sec.get("secret_realms", [])) == 3))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    for name, ok in checks:
        print(("  [PASS] " if ok else "  [FAIL] ") + name)
    return all(ok for _, ok in checks)


def main() -> int:
    no_verify = "--no-verify" in sys.argv
    print("《码上飞升》Release 构建 v%s" % _version())
    target = build()
    print("归档生成：%s（%.0f KB）" % (target, target.stat().st_size / 1024))
    print("启动脚本：%s" % (DIST / "启动游戏.bat"))
    if no_verify:
        print("已跳过启动冒烟验证。")
        return 0
    print("开始启动冒烟验证（zipapp 发行包）...")
    ok = verify(target)
    print("冒烟验证" + ("通过。" if ok else "失败！"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
