"""One-shot JSON bridge between Godot and CodeDaoLab's isolated Python sandbox."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GODOT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = GODOT_ROOT / "runtime"
for import_root in (PROJECT_ROOT, RUNTIME_ROOT):
    if import_root.exists() and str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from game.sandbox import run_player_code  # noqa: E402


def normalize_output(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


def load_challenge(challenge_id: str) -> dict:
    data_path = GODOT_ROOT / "data" / "challenges.json"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parents[1] / "data" / "challenges.json"
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    for challenge in payload.get("challenges", []):
        if challenge.get("id") == challenge_id:
            return challenge
    raise KeyError(f"unknown challenge: {challenge_id}")


def execute(request: dict) -> dict:
    action = str(request.get("action", "run"))
    challenge_id = str(request.get("challenge_id", ""))
    code = str(request.get("code", ""))
    if action not in {"run", "submit"}:
        return {"ok": False, "passed": False, "message": "未知桥接操作。", "status": "internal"}
    if not code.strip():
        return {"ok": False, "passed": False, "message": "真言不可为空。", "status": "syntax"}
    if len(code) > 20_000:
        return {"ok": False, "passed": False, "message": "代码过长，无法刻入玉简。", "status": "internal"}
    challenge = load_challenge(challenge_id)
    result = run_player_code(code, time_limit=5.0, memory_limit_mb=256)
    response = asdict(result)
    response["ok"] = result.status == "ok"
    response["passed"] = False
    response["challenge_id"] = challenge_id
    response["action"] = action
    if action == "submit" and result.status == "ok":
        response["passed"] = normalize_output(result.stdout) == normalize_output(str(challenge.get("expected", "")))
        response["message"] = "代码验证通过。" if response["passed"] else "运行成功，但天地回响与试炼要求不符。"
    return response


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: runner.py request.json response.json", file=sys.stderr)
        return 2
    request_path = Path(sys.argv[1])
    response_path = Path(sys.argv[2])
    try:
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        response = execute(request)
    except Exception as exc:
        response = {
            "ok": False,
            "passed": False,
            "status": "internal",
            "message": "Python 桥接执行失败。",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    response_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = response_path.with_suffix(response_path.suffix + ".tmp")
    temporary.write_text(json.dumps(response, ensure_ascii=False), encoding="utf-8")
    temporary.replace(response_path)
    return 0 if response.get("status") != "internal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
