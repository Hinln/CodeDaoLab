extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	GameState.reset_new_game("试法者", "fire")
	var scene: PackedScene = load("res://scenes/ui/CodeChallengePanel.tscn")
	var panel: CanvasLayer = scene.instantiate()
	add_child(panel)
	panel.open_challenge("awakening_word")
	_check(panel.cast_stage == "观题", "challenge begins at observation stage")
	_check(panel.get_node("%CastingVisual") != null, "spell visualization is present")
	panel.get_node("%CodeEditor").text = "print('天地玄黄，宇宙洪荒。')"
	panel._on_code_changed()
	_check(panel.cast_stage == "落笔", "editing enters inscription stage")
	var syntax_feedback: Dictionary = panel.spell_state_for_result({"status": "syntax", "passed": false}, true)
	_check(str(syntax_feedback.stage).contains("符文断裂"), "syntax error becomes fractured runes")
	var runtime_feedback: Dictionary = panel.spell_state_for_result({"status": "runtime", "passed": false}, true)
	_check(str(runtime_feedback.stage).contains("灵力反冲"), "runtime error becomes qi backlash")
	var timeout_feedback: Dictionary = panel.spell_state_for_result({"status": "timeout", "passed": false}, true)
	_check(str(timeout_feedback.stage).contains("阵法冻结"), "timeout becomes frozen formation")
	var wrong_feedback: Dictionary = panel.spell_state_for_result({"status": "ok", "passed": false}, true)
	_check(str(wrong_feedback.stage).contains("法术偏移"), "wrong output becomes spell deviation")
	var response := PythonBridge.execute_sync("awakening_word", "print('天地玄黄，宇宙洪荒。')", "submit")
	_check(bool(response.get("passed", false)), "real Python validation remains active")
	var success_feedback: Dictionary = panel.spell_state_for_result(response, true)
	_check(str(success_feedback.stage) == "命中", "successful submission becomes a spell hit")
	panel.queue_free()
	if failures.is_empty():
		print("V02_A_SPELLCASTING_PASS: ritual stages, differentiated backlash and real Python")
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
