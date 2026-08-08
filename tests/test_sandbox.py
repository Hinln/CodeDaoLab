# -*- coding: utf-8 -*-
"""沙箱执行模块测试。"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from game import sandbox
from game import config

FUNC_HARNESS = '''
import json as _json
_cases = _json.loads(__CA_CASES__)
_results = []
_fn = globals().get(__CA_FUNC__)
if _fn is None:
    _results.append({"pass": False, "reason": "未找到函数"})
else:
    for _c in _cases:
        try:
            _args = _c.get("args", [])
            _expected = _c.get("expected")
            _actual = _fn(*_args)
            _ok = _actual == _expected
            if not _ok and isinstance(_expected, float) and isinstance(_actual, (int, float)):
                _ok = abs(_actual - _expected) < 1e-9
            _results.append({"pass": _ok, "expected": repr(_expected), "actual": repr(_actual)})
        except Exception as _e:
            _results.append({"pass": False, "error": str(_e)})
print(_json.dumps(_results, ensure_ascii=False))
'''


def cases(pairs):
    return json.dumps([{"args": list(a), "expected": e} for a, e in pairs], ensure_ascii=False)


class TestBasicExecution:
    def test_print_ok(self):
        r = sandbox.run_player_code("print('hello')")
        assert r.is_ok
        assert "hello" in r.stdout

    def test_chinese_output(self):
        r = sandbox.run_player_code("print('天地玄黄，宇宙洪荒。')")
        assert r.is_ok
        assert "天地玄黄，宇宙洪荒。" in r.stdout

    def test_arithmetic(self):
        r = sandbox.run_player_code("print(2 + 3 * 4)")
        assert r.is_ok
        assert "14" in r.stdout

    def test_loop_for(self):
        r = sandbox.run_player_code("for i in range(1, 4):\n    print(i)")
        assert r.is_ok
        assert r.stdout.splitlines() == ["1", "2", "3"]

    def test_loop_while(self):
        code = "n = 1\nwhile n <= 3:\n    print(n)\n    n += 1"
        r = sandbox.run_player_code(code)
        assert r.is_ok
        assert r.stdout.splitlines() == ["1", "2", "3"]

    def test_function_definition(self):
        r = sandbox.run_player_code("def add(a, b):\n    return a + b\nprint(add(2, 3))")
        assert r.is_ok
        assert "5" in r.stdout


class TestErrors:
    def test_syntax_error(self):
        r = sandbox.run_player_code("print('x'")
        assert r.status == "syntax"
        assert "语法错误" in r.message
        assert r.error_line in (1, 2)

    def test_indentation_error(self):
        r = sandbox.run_player_code("def f():\nreturn 1")
        assert r.status == "syntax"
        assert "语法错误" in r.message

    def test_runtime_error(self):
        r = sandbox.run_player_code("x = 1 / 0")
        assert r.status == "runtime"
        assert r.error_class == "ZeroDivisionError"
        assert "division by zero" in r.message

    def test_name_error_has_traceback_detail(self):
        r = sandbox.run_player_code("print(不存在的变量)")
        assert r.status == "runtime"
        assert r.error_class == "NameError"
        assert "不存在的变量" in r.message

    def test_error_line_reported(self):
        r = sandbox.run_player_code("print(1)\nprint(2)\nx = 1 / 0")
        assert r.status == "runtime"
        assert r.error_line == 3


class TestSafety:
    def test_blocked_import(self):
        for mod in ("subprocess", "socket", "pathlib", "ctypes", "importlib", "threading", "gc"):
            r = sandbox.run_player_code("import %s" % mod)
            assert r.status == "runtime", mod
            assert "禁止引入危险模块" in r.message, mod

    def test_blocked_builtins(self):
        for name, code in (
            ("exec", "exec('print(1)')"),
            ("eval", "eval('1+1')"),
            ("compile", "compile('x', 'x', 'exec')"),
        ):
            r = sandbox.run_player_code(code)
            assert r.status == "runtime", name
            assert "禁止" in r.message, name

    def test_file_io_cwd_allowed(self):
        r = sandbox.run_player_code(
            "with open('note.txt', 'w', encoding='utf-8') as f:\n    f.write('x')\n"
            "with open('note.txt', encoding='utf-8') as f:\n    print(f.read())"
        )
        assert r.status == "ok", r.to_dict()
        assert "x" in r.stdout

    def test_file_io_outside_cwd_blocked(self):
        r = sandbox.run_player_code("open('C:/Windows/win.ini', encoding='utf-8').read()")
        assert r.status == "runtime"
        assert "禁止" in r.message

    def test_seed_files_readable(self):
        r = sandbox.run_player_code(
            "with open('卷宗.txt', encoding='utf-8') as f:\n    print(f.read())",
            seed_files={"卷宗.txt": "天之道。\n"},
        )
        assert r.status == "ok", r.to_dict()
        assert "天之道。" in r.stdout

    def test_local_module_import(self):
        code = (
            "with open('spells.py', 'w', encoding='utf-8') as f:\n"
            "    f.write('def flash(x):\\n    return x * 2\\n')\n"
            "import spells\n"
            "print(spells.flash(21))"
        )
        r = sandbox.run_player_code(code)
        assert r.status == "ok", r.to_dict()
        assert r.stdout.strip() == "42"

    def test_os_system_blocked(self):
        r = sandbox.run_player_code("import os\nos.system('dir')")
        assert r.status == "runtime"
        assert "os.system" in r.message

    def test_infinite_loop_timeout(self):
        start = sys.monotonic() if hasattr(sys, "monotonic") else None
        r = sandbox.run_player_code("while True:\n    pass", time_limit=1.5)
        assert r.status == "timeout"
        assert "超时" in r.message
        assert r.wall_time_ms < 6000

    def test_memory_limit(self):
        r = sandbox.run_player_code(
            "x = [0] * 300_000_000\nprint(len(x))", memory_limit_mb=64, time_limit=10
        )
        assert r.status == "memory"
        assert "内存" in r.message

    def test_allowed_benign_modules(self):
        r = sandbox.run_player_code(
            "import math, random, json, collections\n"
            "print(math.sqrt(16), random.randint(1, 2), json.dumps({'a': 1}))"
        )
        assert r.is_ok

    def test_input_injection(self):
        r = sandbox.run_player_code(
            "name = input()\nprint('道友' + name + '，欢迎入道！')", inputs=["云中子"]
        )
        assert r.is_ok
        assert "道友云中子" in r.stdout

    def test_input_exhausted(self):
        r = sandbox.run_player_code("input()\ninput()", inputs=["only"])
        assert r.status == "runtime"
        assert "灵力输入不足" in r.message

    def test_no_project_file_access(self):
        # 尝试读取项目目录文件应被禁止
        r = sandbox.run_player_code("open('CODEX.md')")
        assert r.status == "runtime"

    def test_output_cap(self):
        r = sandbox.run_player_code("print('x' * 200000)", time_limit=5)
        assert len(r.stdout) <= config.MAX_OUTPUT_CHARS + 10


class TestValidationHarness:
    def test_function_pass(self):
        code = "def add(a, b):\n    return a + b"
        r = sandbox.run_validation(code, cases([((2, 3), 5), ((10, 20), 30)]), FUNC_HARNESS, func_name="add")
        assert r.is_ok
        results = json.loads(r.epilogue_output)
        assert len(results) == 2
        assert all(x["pass"] for x in results)

    def test_function_fail(self):
        code = "def add(a, b):\n    return a * b"
        r = sandbox.run_validation(code, cases([((2, 3), 5)]), FUNC_HARNESS, func_name="add")
        assert r.is_ok
        results = json.loads(r.epilogue_output)
        assert results[0]["pass"] is False

    def test_function_missing(self):
        code = "def other(): pass"
        r = sandbox.run_validation(code, cases([((1, 2), 3)]), FUNC_HARNESS, func_name="add")
        assert r.is_ok
        results = json.loads(r.epilogue_output)
        assert results[0]["pass"] is False
        assert "未找到函数" in results[0]["reason"]

    def test_float_tolerance(self):
        code = "def half(x):\n    return x / 2"
        r = sandbox.run_validation(code, cases([((1.0,), 0.5)]), FUNC_HARNESS, func_name="half")
        results = json.loads(r.epilogue_output)
        assert results[0]["pass"] is True

    def test_project_with_inputs(self):
        code = (
            "n = int(input())\n"
            "total = 0\n"
            "for i in range(n):\n"
            "    total += int(input())\n"
            "print(total)"
        )
        r = sandbox.run_validation(code, "[]", "pass", inputs=["3", "10", "20", "30"])
        assert r.is_ok
        assert "60" in r.stdout

    def test_harness_runtime_error(self):
        code = "def f():\n    raise ValueError('boom')"
        r = sandbox.run_validation(code, cases([((), None)]), FUNC_HARNESS, func_name="f")
        results = json.loads(r.epilogue_output)
        assert results[0]["pass"] is False
        assert "boom" in results[0]["error"]
