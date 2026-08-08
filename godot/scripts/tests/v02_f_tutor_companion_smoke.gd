extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	GameState.reset_new_game("问道者", "water", "academy")
	TutorManager.reset_session()
	_check(TutorManager.challenge_greeting("awakening_word").contains("第一次"), "mentor recognizes a first attempt")
	TutorManager.record_attempt("awakening_word", {"status": "syntax", "passed": false})
	TutorManager.record_attempt("awakening_word", {"status": "ok", "passed": false})
	var advice := TutorManager.guidance("awakening_word", {"status": "ok", "passed": false})
	_check(advice.has("mode") and str(advice.text).contains("回响"), "guidance has a graded mode and personal voice")
	TutorManager.record_attempt("awakening_word", {"status": "ok", "passed": true})
	var history: Dictionary = GameState.player.tutor_history
	_check(int(history.total_attempts) == 3 and int(history.total_failures) == 2 and int(history.total_successes) == 1, "attempt history tracks outcomes")
	_check(not JSON.stringify(history).contains("print("), "mentor memory stores no player source code")
	_check(TutorManager.success_reflection("awakening_word").contains("print"), "success reflection names the learned concept")
	_check(TutorManager.reunion_message().contains("3 次"), "reunion response recalls player history")
	_check(TutorManager.chapter_review().contains("问道者") and TutorManager.chapter_review().contains("受阻"), "chapter review reflects the personal journey")
	var hints: Dictionary = DataRepository.get_data("tutor_hints").get("hints", {})
	_check(hints.size() == 6, "offline rules cover every first chapter challenge")
	SaveManager.save_path_override = "user://saves/v02_f_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "mentor history saves")
	TutorManager.clear_player_history()
	_check(SaveManager.load_game(), "mentor history loads")
	_check(int(GameState.player.tutor_history.total_attempts) == 3, "mentor history restores")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	if failures.is_empty():
		print("V02_F_TUTOR_COMPANION_PASS: history, adaptive guidance, reflection and offline fallback")
		get_tree().quit(0)
	else:
		for failure in failures:
			push_error(failure)
		get_tree().quit(1)


func _check(condition: bool, label: String) -> void:
	if condition:
		print("[PASS] ", label)
	else:
		failures.append("[FAIL] " + label)
