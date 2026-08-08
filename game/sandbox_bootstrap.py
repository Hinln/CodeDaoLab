# -*- coding: utf-8 -*-
"""沙箱内核源码。

本文件内容会被父进程写入临时目录并以 ``python -I -u -X utf8 <文件>`` 方式执行，
因此必须完全自包含（不依赖本项目的任何包），玩家代码在其中被真实编译与执行。

屏蔽策略说明：
- 可安全置空 sys.modules 的模块：直接置空（import 即失败）；
- 解释器自举依赖的模块（threading/_thread/warnings/linecache/_io/gc/builtins 等）：
  保留在 sys.modules，但通过 __import__ 守卫拦截玩家导入，并对 io/codecs/_io
  的 open 等危险函数做运行时补丁，sys.modules['builtins'] 替换为安全替身；
- _io.open / _io.open_code 是 CPython 导入机制读取 .pyc/.py 的底层通道，
  使用"标准库目录白名单"守卫：仅允许读取标准库内的文件，玩家无法读写任意路径；
- 说明：本沙箱面向初学者教学场景。纯 Python 进程内无法根除"类继承链内省"
  等高级逃逸手段，生产环境如需对抗性隔离，应叠加容器或低权限账号运行。
"""

BOOTSTRAP_SOURCE = r'''
# -*- coding: utf-8 -*-
"""码上飞升 - 沙箱内核（在 -I 隔离模式下运行）。"""

import sys as _sys
import types as _types
import builtins as _real_builtins

# ---- 0. 读取环境参数与输入 ----
import os as _os_env
import json as _json

_code_marker = _os_env.environ.get("CA_CODE_MARKER", "@@CA_CODE@@")
_epi_marker = _os_env.environ.get("CA_EPILOGUE_MARKER", "@@CA_EPILOGUE@@")
_result_marker = _os_env.environ.get("CA_RESULT_MARKER", "@@CA_RESULT@@")
_inputs = _json.loads(_os_env.environ.get("CA_INPUTS", "[]"))

# 允许导入玩家在洞府内创建的本地模块（-I 隔离模式默认不含脚本目录）
_sys.path.insert(0, _os_env.getcwd())


_stdin_data = _sys.stdin.read()
if _code_marker in _stdin_data:
    _code = _stdin_data.split(_code_marker, 1)[1].split(_epi_marker, 1)[0].lstrip("\n")
else:
    _code = ""
if _epi_marker in _stdin_data:
    _epilogue = _stdin_data.split(_epi_marker, 1)[1].strip("\n")
else:
    _epilogue = ""

_input_index = 0


def _ca_input(prompt=""):
    """替代内建 input()：从预注入队列取输入，避免读取真实标准输入。"""
    global _input_index
    _sys.stdout.write(prompt)
    _sys.stdout.flush()
    if _input_index >= len(_inputs):
        raise RuntimeError("心魔作祟：input() 所需的灵力输入不足（注入的输入已耗尽）。")
    value = _inputs[_input_index]
    _input_index += 1
    return value


# ---- 1. 危险内建函数替换（仅作用于玩家命名空间） ----
def _forbidden(name, tip=""):
    def _blocked(*_args, **_kwargs):
        raise RuntimeError("触犯天条：禁止使用「" + name + "」。" + tip)
    return _blocked


safe_builtins = dict(vars(_real_builtins))
safe_builtins["open"] = _forbidden("open", "修仙界内不可直接读写文件。")
safe_builtins["exec"] = _forbidden("exec", "禁术不可轻用。")
safe_builtins["eval"] = _forbidden("eval", "禁术不可轻用。")
safe_builtins["compile"] = _forbidden("compile", "禁术不可轻用。")
safe_builtins["breakpoint"] = _forbidden("breakpoint", "")
safe_builtins["help"] = _forbidden("help", "")
safe_builtins["input"] = _ca_input
safe_builtins["__import__"] = None  # 稍后替换为守卫版本

# 玩家禁止导入的模块（守卫拦截；其中部分模块因解释器依赖不能置空 sys.modules）
_BLOCKED_MODULES = frozenset({
    # 进程 / 系统
    "subprocess", "multiprocessing", "threading", "_thread", "concurrent",
    "asyncio", "signal", "platform", "sysconfig", "resource", "ctypes",
    "_ctypes", "_winapi", "_subprocess", "msvcrt", "winreg", "winsound",
    "fcntl", "pwd", "grp", "pty", "mmap",
    # 网络
    "socket", "_socket", "ssl", "_ssl", "http", "urllib", "ftplib",
    "smtplib", "smtpd", "telnetlib", "webbrowser", "select", "selectors",
    "wsgiref", "xmlrpc", "cgi", "cgitb", "imaplib", "poplib", "nntplib",
    "mailbox", "mimetypes", "quopri", "uu", "binhex",
    # 文件 / 归档
    "pathlib", "shutil", "glob", "tempfile", "fileinput", "zipfile",
    "tarfile", "gzip", "bz2", "lzma", "zlib", "py_compile", "compileall",
    "zipimport", "dbm", "sqlite3", "shelve", "pickle", "marshal",
    # 动态执行 / 内省
    "importlib", "pkgutil", "runpy", "dis", "code", "codeop", "pdb",
    "bdb", "inspect", "trace", "tracemalloc", "faulthandler", "gc",
    "builtins", "_io", "linecache", "warnings", "dataclasses",
    # 环境 / 安装
    "site", "distutils", "setuptools", "pip", "venv", "ensurepip",
    "idlelib", "tkinter", "curses", "turtledemo",
})

# 解释器自举依赖、不能置空 sys.modules 的模块
_KEEP_MODULES = frozenset({
    "threading", "_thread", "warnings", "linecache", "_io", "gc",
    "builtins", "io", "codecs", "os", "sys", "encodings", "abc",
})

# 可安全置空的模块
_NULL_MODULES = _BLOCKED_MODULES - _KEEP_MODULES

_real_import = _real_builtins.__import__
_real_builtins_open = _real_builtins.open


def _ca_import(name, globals=None, locals=None, fromlist=(), level=0):
    """守卫版 __import__：拦截危险模块，其余走真实导入。"""
    base = (name or "").split(".")[0]
    if base in _BLOCKED_MODULES:
        raise ImportError(
            "触犯天条：禁止引入危险模块「" + base + "」。（大道三千，当脚踏实地）")
    return _real_import(name, globals, locals, fromlist, level)


safe_builtins["__import__"] = _ca_import

# ---- 2. 运行时补丁 + 模块屏蔽 ----
import io as _io_mod
import codecs as _codecs_mod
import traceback as _tb
import _io as _raw_io

# os 模块：环境变量只读 + 危险函数替换
if hasattr(_os_env, "environ"):
    _os_env.environ = _types.MappingProxyType(dict(_os_env.environ))
_CWD_OS = frozenset({
    "getcwd", "listdir", "scandir", "walk",
    "remove", "unlink", "mkdir", "makedirs", "rmdir", "removedirs",
    "rename", "renames", "replace",
})
_real_getcwd = _os_env.getcwd
_real_cwd_os = {_n: getattr(_os_env, _n) for _n in _CWD_OS if hasattr(_os_env, _n)}
_DANGEROUS_OS = frozenset({
    "system", "popen", "startfile", "kill", "abort", "_exit", "fork",
    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve",
    "spawnvp", "spawnvpe", "execl", "execle", "execlp", "execlpe",
    "execv", "execve", "execvp", "execvpe", "remove", "unlink", "rmdir",
    "removedirs", "mkdir", "makedirs", "rename", "renames", "replace",
    "chdir", "fchdir", "chmod", "chown", "lchown", "listdir", "scandir",
    "walk", "open", "fdopen", "close", "closerange", "pipe", "dup",
    "dup2", "read", "write", "lseek", "truncate", "ftruncate", "fsync",
    "fdatasync", "sendfile", "getcwd", "chroot", "setuid", "setgid",
    "setgroups", "initgroups", "getpriority", "setpriority", "nice",
    "getloadavg", "sysconf", "pathconf", "confstr", "cpu_count",
    "sched_getaffinity",
})
for _name in _DANGEROUS_OS:
    if hasattr(_os_env, _name):
        setattr(_os_env, _name, _forbidden("os." + _name, "禁止访问系统能力。"))


def _resolve_in_cwd(path):
    """若路径解析后位于当前修炼洞府（沙箱运行目录）内，返回规范化绝对路径；否则 None。"""
    try:
        norm = _os_env.path.normcase(_os_env.path.realpath(str(path)))
        cwd = _os_env.path.normcase(_os_env.path.realpath(_real_getcwd()))
    except Exception:
        return None
    if norm == cwd or norm.startswith(cwd + _os_env.sep):
        return norm
    return None


def _cwd_open(path, mode="r", *args, **kwargs):
    """洞府内文件守卫：允许读写当前运行目录内的文件。"""
    norm = _resolve_in_cwd(path)
    if norm is None:
        raise RuntimeError("触犯天条：禁止读写修炼洞府（运行目录）之外的文件。")
    if _os_env.path.basename(norm) == "_ca_bootstrap.py":
        raise RuntimeError("触犯天条：不可窥探沙箱内核。")
    return _real_builtins_open(norm, mode, *args, **kwargs)


def _cwd_guard(func, label):
    def _guarded(path, *args, **kwargs):
        norm = _resolve_in_cwd(path)
        if norm is None:
            raise RuntimeError("触犯天条：禁止对「" + label + "」操作洞府之外的文件。")
        return func(norm, *args, **kwargs)
    return _guarded


def _cwd_guard2(func, label):
    def _guarded(src, dst, *args, **kwargs):
        if _resolve_in_cwd(src) is None or _resolve_in_cwd(dst) is None:
            raise RuntimeError("触犯天条：禁止对「" + label + "」操作洞府之外的文件。")
        return func(src, dst, *args, **kwargs)
    return _guarded


# 恢复并守卫安全的洞府内文件操作（原危险表已将其屏蔽）
for _name in _CWD_OS:
    if _name not in _real_cwd_os:
        continue
    _orig = _real_cwd_os[_name]
    if _name == "getcwd":
        setattr(_os_env, _name, _orig)
    elif _name in ("rename", "renames", "replace"):
        setattr(_os_env, _name, _cwd_guard2(_orig, "os." + _name))
    else:
        setattr(_os_env, _name, _cwd_guard(_orig, "os." + _name))

safe_builtins["open"] = _cwd_open
_io_mod.open = _cwd_open
_codecs_mod.open = _cwd_open

# _io.open / _io.open_code / _io.FileIO 是导入机制读取 .pyc/.py 的底层通道：
# 允许访问标准库目录与当前洞府目录（本地模块导入 + 洞府内文件读写）。
_stdlib_dir = _os_env.path.normcase(_os_env.path.abspath(_os_env.path.dirname(_os_env.__file__)))


def _stdlib_guard(func, label):
    """导入通道守卫：标准库目录与当前洞府目录内可访问（支持本地模块导入）。"""
    def _guarded(path, *args, **kwargs):
        norm = _os_env.path.normcase(_os_env.path.abspath(str(path)))
        if norm.startswith(_stdlib_dir):
            return func(norm, *args, **kwargs)
        cwd_norm = _resolve_in_cwd(path)
        if cwd_norm is not None:
            return func(cwd_norm, *args, **kwargs)
        raise RuntimeError("触犯天条：禁止使用「" + label + "」读写文件。")
    return _guarded


def _stdlib_open(path, *args, **kwargs):
    # builtins.open 替身：允许标准库与当前洞府目录内的文件
    norm = _os_env.path.normcase(_os_env.path.abspath(str(path)))
    if norm.startswith(_stdlib_dir):
        return _real_builtins_open(norm, *args, **kwargs)
    cwd_norm = _resolve_in_cwd(path)
    if cwd_norm is not None:
        return _real_builtins_open(cwd_norm, *args, **kwargs)
    raise FileNotFoundError(2, "文件不在可访问范围内", str(path))

_raw_io.open = _stdlib_guard(_raw_io.open, "_io.open")
_raw_io.open_code = _stdlib_guard(_raw_io.open_code, "_io.open_code")
_raw_io.FileIO = _stdlib_guard(_raw_io.FileIO, "_io.FileIO")

# 可安全置空的模块：直接置空
for _m in _NULL_MODULES:
    _sys.modules.pop(_m, None)
    _sys.modules[_m] = None

# sys.modules['builtins'] 替换为安全替身（只暴露安全内建）
_builtins_shim = _types.ModuleType("builtins")
for _name, _value in safe_builtins.items():
    setattr(_builtins_shim, _name, _value)
_builtins_shim.open = _stdlib_open
_sys.modules["builtins"] = _builtins_shim

# ---- 3. 玩家命名空间与执行 ----
_g = {"__name__": "__main__", "__builtins__": safe_builtins}

_main_mod = _types.ModuleType("__main__")
_main_mod.__dict__.update(_g)
_sys.modules["__main__"] = _main_mod

_result = {"status": "ok", "message": "", "detail": "", "error_class": "", "error_line": 0, "epilogue_output": ""}


def _fmt_syntax_error(exc):
    text = (exc.text or "").rstrip("\n")
    where = ("第 %d 行 " % exc.lineno) if exc.lineno else ""
    hint = ""
    if exc.msg and "expected" in exc.msg:
        hint = "（可能是少了括号、引号或冒号）"
    return {
        "message": "灵气紊乱（语法错误）：%s%s%s%s" % (
            where, exc.msg or "", (" —— " + text) if text else "", hint),
        "detail": "",
        "error_class": "SyntaxError",
        "error_line": exc.lineno or 0,
    }


def _fmt_runtime(exc, status="runtime"):
    name = type(exc).__name__
    message = str(exc) or name
    detail = ""
    line = 0
    try:
        tbe = _tb.TracebackException(type(exc), exc, exc.__traceback__)
        frames = [f for f in _tb.extract_tb(exc.__traceback__)
                  if f.filename in ("<修士代码>", "<试炼台>")]
        if frames:
            line = frames[-1].lineno or 0
        tbe.stack = _tb.StackSummary.from_list(frames)
        detail = "".join(tbe.format()).strip()
    except Exception:
        detail = ""
    return {"status": status, "error_class": name, "message": message, "detail": detail, "error_line": line}


try:
    _compiled = compile(_code, "<修士代码>", "exec")
except SyntaxError as _e:
    _result.update(_fmt_syntax_error(_e))
    _result["status"] = "syntax"
except BaseException as _e:
    _result.update(_fmt_runtime(_e, "internal"))
else:
    try:
        exec(_compiled, _g, _g)
    except SyntaxError as _e:
        _result.update(_fmt_syntax_error(_e))
        _result["status"] = "syntax"
    except SystemExit as _e:
        code = _e.code
        if code in (None, 0):
            _result["status"] = "ok"
        else:
            _result.update(_fmt_runtime(_e, "runtime"))
    except BaseException as _e:
        _result.update(_fmt_runtime(_e, "runtime"))
    else:
        if _epilogue.strip():
            _buf = _io_mod.StringIO()
            _old_out = _sys.stdout
            _sys.stdout = _buf
            try:
                exec(compile(_epilogue, "<试炼台>", "exec"), _g, _g)
            except BaseException as _e:
                _result.update(_fmt_runtime(_e, "runtime"))
            finally:
                _sys.stdout = _old_out
            _result["epilogue_output"] = _buf.getvalue()

_sys.stdout.write(_result_marker + _json.dumps(_result, ensure_ascii=False))
_sys.stdout.flush()
_sys.exit(0)
'''


def get_bootstrap_source() -> str:
    """返回沙箱内核源码（供父进程写入临时文件后以子进程方式执行）。"""
    return BOOTSTRAP_SOURCE
