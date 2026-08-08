# -*- coding: utf-8 -*-
"""安全 Python 执行沙箱（父进程侧）。

设计要点：
- 玩家代码在独立子进程中以 ``python -I -u -X utf8`` 隔离模式真实执行；
- 通过沙箱内核（sandbox_bootstrap）屏蔽危险模块与危险内建函数；
- 超时机制防止无限循环（communicate 超时后强制结束进程）；
- 内存限制：Windows 下优先使用 Job Object（进程内存上限），失败则回退为
  轮询监控（GetProcessMemoryInfo）；POSIX 下使用 resource.setrlimit；
- 玩家代码经标准输入传入，cwd 为全新临时目录，环境变量最小化。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass

from . import config
from .sandbox_bootstrap import get_bootstrap_source

# 结果标记：防止玩家伪造输出干扰解析
_RESULT_MARKER = "__CA_RESULT_%s__" % uuid.uuid4().hex[:12]

# 内存超限时 Windows 的进程终止码 (STATUS_COMMITMENT_LIMIT)
_STATUS_COMMITMENT_LIMIT = 0xC000012D


@dataclass
class RunResult:
    """一次代码运行的结果。"""

    status: str = "ok"           # ok | syntax | runtime | timeout | memory | internal
    stdout: str = ""
    stderr: str = ""
    message: str = ""            # 面向玩家的中文摘要
    detail: str = ""             # 补充信息（如 traceback 片段）
    error_class: str = ""
    error_line: int = 0
    exit_code: int = 0
    wall_time_ms: int = 0
    epilogue_output: str = ""    # 验证片段输出（仅验证运行时使用）

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "message": self.message,
            "detail": self.detail,
            "error_class": self.error_class,
            "error_line": self.error_line,
            "exit_code": self.exit_code,
            "wall_time_ms": self.wall_time_ms,
        }


def _windows_job_object(memory_limit_mb: int):
    """创建带内存上限与“关闭即杀”的 Job Object；失败返回 None。"""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        SIZE_T = ctypes.c_size_t

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", SIZE_T),
                ("MaximumWorkingSetSize", SIZE_T),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", SIZE_T),
                ("JobMemoryLimit", SIZE_T),
                ("PeakProcessMemoryUsed", SIZE_T),
                ("PeakJobMemoryUsed", SIZE_T),
            ]

        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
        JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

        h_job = kernel32.CreateJobObjectW(None, None)
        if not h_job:
            return None
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        info.ProcessMemoryLimit = int(memory_limit_mb) * 1024 * 1024
        ok = kernel32.SetInformationJobObject(
            h_job,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            kernel32.CloseHandle(h_job)
            return None

        def _assign(handle: int) -> bool:
            return bool(kernel32.AssignProcessToJobObject(h_job, handle))

        def _close():
            try:
                kernel32.CloseHandle(h_job)
            except Exception:
                pass

        return _assign, _close
    except Exception:
        return None


def _windows_process_memory_mb(handle: int) -> float:
    """获取进程当前工作集内存（MB）。"""
    try:
        import ctypes
        from ctypes import wintypes

        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        SIZE_T = ctypes.c_size_t

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", SIZE_T),
                ("WorkingSetSize", SIZE_T),
                ("QuotaPeakPagedPoolUsage", SIZE_T),
                ("QuotaPagedPoolUsage", SIZE_T),
                ("QuotaPeakNonPagedPoolUsage", SIZE_T),
                ("QuotaNonPagedPoolUsage", SIZE_T),
                ("PagefileUsage", SIZE_T),
                ("PeakPagefileUsage", SIZE_T),
            ]

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return 0.0
        return pmc.WorkingSetSize / (1024 * 1024)
    except Exception:
        return 0.0


def _monitor_memory(proc, limit_mb: float, stop: threading.Event) -> str:
    """轮询监控子进程内存，超限则结束进程并返回原因。"""
    try:
        handle = proc._handle  # Windows 下为句柄整数
        while not stop.wait(0.05):
            try:
                usage = _windows_process_memory_mb(handle)
                if usage > limit_mb:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return "memory"
            except Exception:
                return ""
        return ""
    except Exception:
        return ""


def _posix_preexec(time_limit: float, memory_limit_mb: float):
    def _setup():
        try:
            import resource

            cpu = max(1, int(time_limit) + 2)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
            mem = int(memory_limit_mb) * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        except Exception:
            pass

    return _setup


def _safe_seed_relpath(rel_path: str) -> str:
    """将任务数据中的相对路径清洗为安全路径（防目录穿越，数据为受信来源）。"""
    rel_path = str(rel_path).replace("\\", "/")
    parts = [p for p in rel_path.split("/") if p not in ("", ".", "..")]
    return os.path.join(*parts) if parts else "_seed.txt"


def run_player_code(
    code: str,
    inputs: list | tuple = (),
    time_limit: float | None = None,
    memory_limit_mb: int | None = None,
    epilogue: str = "",
    seed_files: dict | None = None,
) -> RunResult:
    """在隔离子进程中真实执行玩家代码，返回结构化结果。"""
    time_limit = float(time_limit if time_limit is not None else config.DEFAULT_TIME_LIMIT)
    memory_limit_mb = int(memory_limit_mb or config.DEFAULT_MEMORY_LIMIT_MB)

    code_marker = "__CA_CODE_%s__" % uuid.uuid4().hex[:8]
    epi_marker = "__CA_EPILOGUE_%s__" % uuid.uuid4().hex[:8]

    env = {
        "CA_CODE_MARKER": code_marker,
        "CA_EPILOGUE_MARKER": epi_marker,
        "CA_RESULT_MARKER": _RESULT_MARKER,
        "CA_INPUTS": json.dumps(list(inputs), ensure_ascii=False),
        "PATH": os.environ.get("PATH", ""),
        "SystemRoot": os.environ.get("SystemRoot", ""),
        "TEMP": tempfile.gettempdir(),
        "TMP": tempfile.gettempdir(),
    }

    stdin_payload = (
        code_marker + "\n" + code + "\n" + epi_marker + "\n" + epilogue
    ).encode("utf-8")

    temp_dir = tempfile.mkdtemp(prefix="ca_sandbox_")
    bootstrap_path = os.path.join(temp_dir, "_ca_bootstrap.py")
    with open(bootstrap_path, "w", encoding="utf-8") as f:
        f.write(get_bootstrap_source())
    for rel_path, content in (seed_files or {}).items():
        target = os.path.join(temp_dir, _safe_seed_relpath(rel_path))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    proc = None
    monitor_stop = threading.Event()
    monitor = None
    job_assign, job_close = None, None

    start = time.monotonic()
    try:
        cmd = [sys.executable, "-I", "-E", "-u", "-X", "utf8", bootstrap_path]
        if os.name == "nt":
            job = _windows_job_object(memory_limit_mb)
            if job is not None:
                job_assign, job_close = job

        kwargs = {}
        if os.name == "posix":
            kwargs["preexec_fn"] = _posix_preexec(time_limit, memory_limit_mb)

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_dir,
            env=env,
            creationflags=creationflags,
            **kwargs,
        )

        if job_assign is not None:
            try:
                job_assign(proc._handle)
            except Exception:
                job_assign = None

        if os.name == "nt" and job_assign is None:
            monitor = threading.Thread(
                target=_monitor_memory, args=(proc, memory_limit_mb, monitor_stop), daemon=True
            )
            monitor.start()

        try:
            stdout_b, stderr_b = proc.communicate(input=stdin_payload, timeout=time_limit)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.communicate(timeout=3)
            except Exception:
                pass
            result = RunResult(
                status="timeout",
                message="心魔入体（运行超时）：疑似无限循环或运行过慢，已强行中断。"
                "请检查循环条件与退出条件。",
            )
            result.wall_time_ms = int((time.monotonic() - start) * 1000)
            return result

        wall_ms = int((time.monotonic() - start) * 1000)
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")

        exit_code = proc.returncode or 0

        # 解析内核结果
        status = "ok"
        message = ""
        detail = ""
        error_class = ""
        error_line = 0
        epilogue_output = ""
        if _RESULT_MARKER in stdout:
            head, _, tail = stdout.partition(_RESULT_MARKER)
            stdout = head
            try:
                payload = json.loads(tail.strip())
            except Exception:
                payload = {}
            status = payload.get("status", "ok")
            message = payload.get("message", "")
            detail = payload.get("detail", "")
            error_class = payload.get("error_class", "")
            error_line = payload.get("error_line", 0)
            epilogue_output = payload.get("epilogue_output", "")
        elif exit_code != 0:
            status = "internal"
            message = "内核异常退出（退出码 %d）。%s" % (exit_code, stderr.strip()[:300])

        # 内存超限判定
        if os.name == "nt" and exit_code == _STATUS_COMMITMENT_LIMIT:
            status = "memory"
            message = "灵力耗尽（内存超限）：程序占用内存超过 %d MB，已强行中断。" % memory_limit_mb
        if status == "runtime" and error_class == "MemoryError":
            status = "memory"
            message = "灵力耗尽（内存超限）：程序申请内存超出限制（%d MB），已中断。" % memory_limit_mb

        # 输出上限
        if len(stdout) > config.MAX_OUTPUT_CHARS:
            stdout = stdout[: config.MAX_OUTPUT_CHARS]
            message = (message + " " if message else "") + "（输出过长，已截断）"

        return RunResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            message=message,
            detail=detail,
            error_class=error_class,
            error_line=error_line,
            exit_code=exit_code,
            wall_time_ms=wall_ms,
            epilogue_output=epilogue_output,
        )
    finally:
        if monitor is not None:
            monitor_stop.set()
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
        if job_close is not None:
            job_close()
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def run_validation(code, cases_json, harness, inputs=(), time_limit=None, memory_limit_mb=None, func_name=None, method=None, seed_files=None):
    """Run player code plus validation harness and return a structured result.

    Placeholders ``__CA_CASES__`` / ``__CA_FUNC__`` / ``__CA_METHOD__`` inside
    harness are replaced with JSON-escaped string literals (safe to embed).
    """
    epilogue = harness.replace("__CA_CASES__", json.dumps(cases_json, ensure_ascii=False))
    if func_name:
        epilogue = epilogue.replace("__CA_FUNC__", json.dumps(func_name, ensure_ascii=False))
    epilogue = epilogue.replace("__CA_METHOD__", "None" if method is None else json.dumps(method, ensure_ascii=False))
    return run_player_code(
        code,
        inputs=inputs,
        time_limit=time_limit,
        memory_limit_mb=memory_limit_mb,
        epilogue=epilogue,
        seed_files=seed_files,
    )
