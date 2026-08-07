# -*- coding: utf-8 -*-
"""Flask 游戏服务：REST API + 前端静态资源。"""

from __future__ import annotations

import mimetypes
import os
import threading

from flask import Flask, Response, abort, jsonify, request

from . import achievements, ai, config, curriculum, dialogues, items, npcs, sandbox, save, secret_realms, tasks, techniques
from .player import Player

_state_lock = threading.Lock()
_current_player: Player | None = None
_current_slot: str = config.DEFAULT_SLOT
_secret_challenges: dict[str, dict] = {}


def _build_state(player: Player) -> dict:
    """构造前端所需的完整游戏状态。"""
    realm = curriculum.realm_by_key(player.realm_key)
    current = tasks.current_task_id(player)
    current_task = curriculum.get_task(current) if current else None

    debug_defs = [curriculum.get_task(t) for t in tasks.unlocked_debug_tasks(player)]
    waves = []
    for wave in sorted(curriculum.tribulation_waves().values(), key=lambda w: w["order"]):
        wave_task = curriculum.get_task(wave["task"])
        waves.append({
            "key": wave["key"],
            "title": wave["title"],
            "order": wave["order"],
            "task_id": wave["task"],
            "intro": (wave_task or {}).get("story", ""),
            "passed": wave["task"] in player.tribulation_passed,
            "current": wave["key"] == tasks.current_wave_key(player),
        })

    trib = curriculum.tribulation()
    branch_defs = [curriculum.get_task(t) for t in tasks.unlocked_branch_tasks(player)]
    tech_list = []
    for tech in techniques.all_techniques():
        tech_list.append(dict(tech, unlocked=tech["id"] in player.techniques))
    item_list = []
    for item_id, item in items.items().items():
        item_list.append(dict(item, id=item_id, count=player.items.get(item_id, 0)))
    return {
        "player": player.to_dict(),
        "realm": {
            "key": realm["key"],
            "name": realm["name"],
            "order": realm["order"],
            "intro": realm["intro"],
            "teaching": realm["teaching"],
            "major": curriculum.major_realm_for(player.realm_key),
        },
        "current_task": current_task,
        "realm_complete": tasks.is_realm_complete(player, player.realm_key),
        "pending_breakthrough": player.pending_breakthrough,
        "debug_tasks": [{"id": d["id"], "title": d["title"], "story": d["story"]} for d in debug_defs],
        "branch_tasks": [{"id": t["id"], "title": t["title"], "story": t["story"]} for t in branch_defs],
        "techniques": tech_list,
        "items": item_list,
        "achievements": achievements.all_with_status(player),
        "secret_realms": _secret_summary(player),
        "tribulation": {
            "name": trib["name"],
            "intro": trib["intro"],
            "unlocked": tasks.is_tribulation_unlocked(player),
            "waves": waves,
        },
        "meta": curriculum.curriculum()["meta"],
        "realm_names": {r["key"]: r["name"] for r in curriculum.realms()},
        "has_save": save.save_exists(),
        "slots": [s["slot"] for s in save.list_saves()],
    }


def _read_static(rel_path: str) -> bytes | None:
    """读取静态资源：zipapp 模式下从归档内读取，源码模式读磁盘。"""
    rel_path = rel_path.replace("\\", "/")
    if config.ZIP_MODE:
        try:
            from importlib import resources
            return resources.files("static").joinpath(rel_path).read_bytes()
        except Exception:
            return None
    full = os.path.join(config.STATIC_DIR, rel_path)
    try:
        with open(full, "rb") as f:
            return f.read()
    except OSError:
        return None


def _require_player():
    global _current_player
    if _current_player is None:
        loaded = save.load_game(_current_slot)
        if loaded is None:
            return None
        _current_player = loaded
    return _current_player


def _visible_task(player: Player, task_id: str) -> dict | None:
    task = curriculum.get_task(task_id)
    if task is None:
        return None
    if tasks.task_visible_kind(player, task):
        return task
    return None


def _resolve_task(player: Player, task_id: str) -> dict | None:
    """按任务 id 解析可见任务；秘境挑战（secret:<realm_id>）查当前会话。"""
    if task_id.startswith("secret:"):
        return _secret_challenges.get(task_id.split(":", 1)[1])
    return _visible_task(player, task_id)


def _secret_summary(player: Player) -> list[dict]:
    """秘境总览：是否已解锁、当前境界可否进入、通关次数。"""
    summary = []
    for realm_id, realm in secret_realms.secret_realms().items():
        summary.append({
            "id": realm["id"],
            "name": realm["name"],
            "icon": realm.get("icon", "🌀"),
            "desc": realm.get("desc", ""),
            "min_realm": realm.get("min_realm"),
            "max_realm": realm.get("max_realm"),
            "unlocked": realm["id"] in player.secret_unlocked,
            "enterable": secret_realms.is_enterable(player, realm),
            "cleared": int(player.secret_log.get(realm_id, 0)),
        })
    return summary


def create_app() -> Flask:
    if config.ZIP_MODE:
        app = Flask(__name__, static_folder=None)
    else:
        app = Flask(__name__, static_folder=config.STATIC_DIR, static_url_path="/static")

    @app.get("/")
    def index():
        data = _read_static("index.html")
        if data is None:
            return jsonify({"error": "静态资源缺失，发行包可能不完整"}), 500
        return Response(data, mimetype="text/html; charset=utf-8")

    if config.ZIP_MODE:

        @app.get("/static/<path:filename>")
        def static_file(filename):
            data = _read_static(filename)
            if data is None:
                return jsonify({"error": "资源不存在"}), 404
            mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            return Response(data, mimetype=mime)

    @app.get("/api/state")
    def api_state():
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"player": None, "slots": [s["slot"] for s in save.list_saves()]})
            return jsonify(_build_state(player))

    @app.get("/api/slots")
    def api_slots():
        """列出所有存档槽位（含角色摘要）。"""
        with _state_lock:
            return jsonify({"slots": save.list_saves()})

    @app.post("/api/game/new")
    def api_new_game():
        global _current_player, _current_slot
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()[:20] or "无名散修"
        spirit_root = (data.get("spirit_root") or "金").strip()[:4]
        slot = (data.get("slot") or config.DEFAULT_SLOT).strip()[:40] or config.DEFAULT_SLOT
        with _state_lock:
            _current_slot = slot
            _current_player = Player(name=name, spirit_root=spirit_root)
            techniques.learn_realm_technique(_current_player, _current_player.realm_key)
            save.save_game(_current_player, slot)
            return jsonify(_build_state(_current_player))

    @app.post("/api/game/save")
    def api_save():
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚无角色可保存"}), 400
            saved_at = save.save_game(player, _current_slot)
            return jsonify({"ok": True, "saved_at": saved_at})

    @app.post("/api/game/load")
    def api_load():
        global _current_player, _current_slot
        data = request.get_json(silent=True) or {}
        slot = (data.get("slot") or config.DEFAULT_SLOT).strip()[:40] or config.DEFAULT_SLOT
        with _state_lock:
            player = save.load_game(slot)
            if player is None:
                return jsonify({"error": "没有可读取的存档"}), 404
            _current_slot = slot
            _current_player = player
            return jsonify(_build_state(player))

    @app.post("/api/game/delete")
    def api_delete():
        global _current_player
        data = request.get_json(silent=True) or {}
        slot = (data.get("slot") or config.DEFAULT_SLOT).strip()[:40] or config.DEFAULT_SLOT
        with _state_lock:
            if not save.delete_save(slot):
                return jsonify({"error": "该槽位没有存档"}), 404
            if slot == _current_slot:
                _current_player = None
            return jsonify({"ok": True})

    @app.get("/api/curriculum")
    def api_curriculum():
        """返回课程总览（境界 + 任务清单），供界面浏览。"""
        realms = []
        for realm in curriculum.realms():
            realms.append({
                "key": realm["key"],
                "name": realm["name"],
                "order": realm["order"],
                "tasks": realm["tasks"],
            })
        return jsonify({
            "realms": realms,
            "debug_tasks": curriculum.tasks()["debug_tasks"],
            "tribulation_waves": curriculum.tribulation_waves(),
        })

    @app.get("/api/npcs")
    def api_npcs():
        """NPC 列表。"""
        with _state_lock:
            return jsonify({"npcs": npcs.all_npcs()})

    @app.get("/api/dialogues/<npc_id>")
    def api_dialogue_enter(npc_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            if not dialogues.get_tree(npc_id):
                return jsonify({"error": "该 NPC 没有对话"}), 404
            result = dialogues.enter(player, npc_id)
            return jsonify({"dialogue": result})

    @app.post("/api/dialogues/<npc_id>/choose")
    def api_dialogue_choose(npc_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            if not dialogues.get_tree(npc_id):
                return jsonify({"error": "该 NPC 没有对话"}), 404
            data = request.get_json(silent=True) or {}
            try:
                result = dialogues.choose(
                    player, npc_id, data.get("node_id", "start"), int(data.get("option_index", -1))
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            new_achievements = achievements.check_all(player)
            save.save_game(player, _current_slot)
            return jsonify({
                "dialogue": result,
                "state": _build_state(player),
                "new_achievements": new_achievements,
            })

    @app.get("/api/achievements")
    def api_achievements():
        """成就总览。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            return jsonify({"achievements": achievements.all_with_status(player)})

    @app.get("/api/techniques")
    def api_techniques():
        """功法总览（藏经阁）。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            tech_list = []
            for tech in techniques.all_techniques():
                tech_list.append(dict(tech, unlocked=tech["id"] in player.techniques))
            return jsonify({"techniques": tech_list})

    @app.get("/api/items")
    def api_items():
        """道具背包（含定义）。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            item_list = []
            for item_id, item in items.items().items():
                item_list.append(dict(item, id=item_id, count=player.items.get(item_id, 0)))
            return jsonify({"items": item_list})

    @app.post("/api/items/<item_id>/use")
    def api_item_use(item_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            result = items.use_item(player, item_id)
            if not result["used"]:
                return jsonify({"error": result["message"]}), 400
            new_achievements = achievements.check_all(player, {"item_used": True})
            save.save_game(player, _current_slot)
            return jsonify({
                "result": result,
                "state": _build_state(player),
                "new_achievements": new_achievements,
            })

    @app.get("/api/secret-realms")
    def api_secret_realms():
        """秘境总览（解锁/门槛/通关次数）。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            return jsonify({"secret_realms": _secret_summary(player)})

    @app.post("/api/secret-realms/<realm_id>/enter")
    def api_secret_enter(realm_id):
        """进入秘境：生成新挑战并返回（不含参考答案与校验结构）。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            realm = secret_realms.get_realm(realm_id)
            if realm is None:
                return jsonify({"error": "秘境不存在"}), 404
            if not secret_realms.is_enterable(player, realm):
                return jsonify({"error": "此秘境尚未开启，或你的境界不在其门槛之内"}), 403
            try:
                challenge = secret_realms.generate_challenge(realm_id)
            except RuntimeError as e:
                return jsonify({"error": str(e)}), 500
            _secret_challenges[realm_id] = challenge
            return jsonify({"challenge": secret_realms.sanitize(challenge)})

    @app.post("/api/secret-realms/<realm_id>/run")
    def api_secret_run(realm_id):
        """运行玩家代码（不判定对错）。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            challenge = _secret_challenges.get(realm_id)
            if challenge is None:
                return jsonify({"error": "请先进入秘境"}), 400
            data = request.get_json(silent=True) or {}
            code = data.get("code") or ""
            r = sandbox.run_player_code(
                code,
                inputs=list(challenge.get("check", {}).get("inputs", [])),
                time_limit=float(challenge.get("time_limit", 5)),
                seed_files=challenge.get("check", {}).get("seed_files"),
            )
            return jsonify({"run": r.to_dict()})

    @app.post("/api/secret-realms/<realm_id>/submit")
    def api_secret_submit(realm_id):
        """提交验证：通过则结算奖励并记录通关。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            realm = secret_realms.get_realm(realm_id)
            if realm is None:
                return jsonify({"error": "秘境不存在"}), 404
            challenge = _secret_challenges.get(realm_id)
            if challenge is None:
                return jsonify({"error": "请先进入秘境"}), 400
            data = request.get_json(silent=True) or {}
            code = data.get("code") or ""
            outcome = tasks.validate_task(challenge, code)
            new_achievements = []
            events = {}
            if not outcome.passed:
                player.record_failure("secret:" + realm_id)
                player.add_mindset(-2)
                player.reset_streak()
            else:
                player.clear_attempts("secret:" + realm_id)
                player.record_success()
                events = secret_realms.apply_clear(player, realm_id, challenge)
                new_achievements = achievements.check_all(player)
                save.save_game(player, _current_slot)
            return jsonify({
                "outcome": outcome.to_dict(),
                "events": events,
                "state": _build_state(player),
                "new_achievements": new_achievements,
            })

    @app.post("/api/ai/guidance")
    def api_ai_guidance():
        """求师尊指点：返回分级引导文本。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            data = request.get_json(silent=True) or {}
            task = _resolve_task(player, data.get("task_id", ""))
            if task is None:
                return jsonify({"error": "该任务当前不可见或不存在"}), 404
            attempts = player.attempt_count(task["id"])
            tutor = ai.create_tutor()
            if isinstance(tutor, ai.LocalTutor):
                level = tutor.level_for(player, attempts)
            else:
                level = min(4, max(1, int(data.get("hint_level", 0) or 1)))
            text = tutor.guidance(player, {
                "task_id": task["id"],
                "title": task.get("title", ""),
                "hints": task.get("hints", []),
                "attempts": attempts,
                "hint_level": data.get("hint_level"),
                "realm_key": player.realm_key,
                "no_solution": bool(task.get("no_solution", False)),
            })
            return jsonify({"provider": tutor.name, "level": level, "text": text})

    @app.post("/api/ai/analyze")
    def api_ai_analyze():
        """请师尊诊断：运行代码并给出引导式错误分析。"""
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            data = request.get_json(silent=True) or {}
            task = _resolve_task(player, data.get("task_id", ""))
            if task is None:
                return jsonify({"error": "该任务当前不可见或不存在"}), 404
            code = data.get("code") or ""
            r = sandbox.run_player_code(
                code,
                inputs=list(task.get("check", {}).get("inputs", [])),
                time_limit=float(task.get("time_limit", 5)),
                seed_files=task.get("check", {}).get("seed_files"),
            )
            tutor = ai.create_tutor()
            analysis = tutor.error_analysis(player, r.to_dict(), task)
            return jsonify({"analysis": analysis, "run": r.to_dict(), "provider": tutor.name})

    @app.get("/api/tasks/<task_id>")
    def api_task(task_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            task = _visible_task(player, task_id)
            if task is None:
                return jsonify({"error": "该任务当前不可见或不存在"}), 404
            return jsonify(task)

    @app.post("/api/tasks/<task_id>/run")
    def api_task_run(task_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            task = _visible_task(player, task_id)
            if task is None:
                return jsonify({"error": "该任务当前不可见或不存在"}), 404
            data = request.get_json(silent=True) or {}
            code = data.get("code") or ""
            inputs = data.get("inputs")
            if inputs is None:
                inputs = task.get("check", {}).get("inputs", [])
            r = sandbox.run_player_code(
                code,
                inputs=inputs,
                time_limit=float(task.get("time_limit", 5)),
                seed_files=task.get("check", {}).get("seed_files"),
            )
            return jsonify({"run": r.to_dict()})

    @app.post("/api/tasks/<task_id>/submit")
    def api_task_submit(task_id):
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            task = _visible_task(player, task_id)
            if task is None:
                return jsonify({"error": "该任务当前不可见或不存在"}), 404
            data = request.get_json(silent=True) or {}
            code = data.get("code") or ""
            outcome = tasks.validate_task(task, code)
            new_achievements = []
            events = {}
            if not outcome.passed:
                player.record_failure(task_id)
                player.add_mindset(-2)
                player.reset_streak()
            else:
                player.clear_attempts(task_id)
                player.record_success()
                kind = task.get("kind", "main")
                if kind == "debug":
                    events = tasks.complete_debug_task(player, task)
                elif kind == "wave":
                    events = tasks.complete_wave(player, task)
                elif kind == "branch":
                    events = tasks.complete_branch_task(player, task)
                else:
                    events = tasks.complete_main_task(player, task)
                new_achievements = achievements.check_all(player)
                save.save_game(player, _current_slot)
            return jsonify({
                "outcome": outcome.to_dict(),
                "events": events,
                "state": _build_state(player),
                "new_achievements": new_achievements,
            })

    @app.post("/api/breakthrough")
    def api_breakthrough():
        with _state_lock:
            player = _require_player()
            if player is None:
                return jsonify({"error": "尚未创建角色"}), 400
            try:
                event = tasks.breakthrough(player)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            new_achievements = achievements.check_all(player)
            save.save_game(player, _current_slot)
            return jsonify({
                "event": event,
                "state": _build_state(player),
                "new_achievements": new_achievements,
            })

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "路径不存在"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "服务器内部错误"}), 500

    return app


def run(host: str | None = None, port: int | None = None):
    """启动开发服务器。"""
    app = create_app()
    app.run(
        host=host or config.HOST,
        port=port or config.PORT,
        debug=False,
        threaded=True,
        use_reloader=False,
    )
