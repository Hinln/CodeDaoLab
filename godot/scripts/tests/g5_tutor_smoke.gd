extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	GameState.reset_new_game("问心者", "water")
	TutorManager.reset_session()
	var unique_hints: Dictionary = {}
	for expected_level in range(1, 5):
		var advice := TutorManager.guidance("awakening_word")
		_check(int(advice.level) == expected_level, "guidance reaches L%d" % expected_level)
		unique_hints[str(advice.text)] = true
	_check(unique_hints.size() == 4, "four guidance levels have distinct content")
	var syntax_text := TutorManager.diagnose({"status": "syntax", "error_line": 2})
	_check(syntax_text.contains("语法错误") and syntax_text.contains("第 2 行"), "syntax diagnosis identifies line")
	var runtime_text := TutorManager.diagnose({"status": "runtime", "error_class": "NameError"})
	_check(runtime_text.contains("NameError"), "runtime diagnosis identifies exception")
	_check(TutorManager.diagnose({"status": "timeout"}).contains("循环"), "timeout diagnosis is actionable")
	_check(TutorManager.diagnose({"status": "ok", "passed": false}).contains("输出"), "wrong-output diagnosis is actionable")
	GameState.set_player_value("mindset", 20)
	TutorManager.reset_session()
	_check(int(TutorManager.guidance("spirit_vessel").level) == 3, "low mindset accelerates to L3")
	GameState.set_player_value("mindset", 100)
	GameState.set_player_value("comprehension", 20)
	TutorManager.reset_session()
	_check(int(TutorManager.guidance("cycle_meridian").level) == 2, "high comprehension accelerates one level")
	var hint_data: Dictionary = DataRepository.get_data("tutor_hints").get("hints", {})
	_check(hint_data.size() == 6 and hint_data.values().all(func(levels: Array) -> bool: return levels.size() == 4), "all six first-chapter challenges have four hint levels")
	if failures.is_empty():
		print("G5_TUTOR_SMOKE_PASS: graded guidance, adaptive pacing and structured diagnosis")
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
