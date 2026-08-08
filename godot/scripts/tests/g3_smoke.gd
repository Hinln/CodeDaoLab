extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var correct := PythonBridge.execute_sync("awakening_word", "print('天地玄黄，宇宙洪荒。')", "submit")
	_check(correct.get("status", "") == "ok" and bool(correct.get("passed", false)), "real Python bridge accepts correct output")
	var wrong := PythonBridge.execute_sync("awakening_word", "print('伪言')", "submit")
	_check(wrong.get("status", "") == "ok" and not bool(wrong.get("passed", false)), "real Python bridge rejects wrong output")
	var syntax := PythonBridge.execute_sync("awakening_word", "print(", "submit")
	_check(syntax.get("status", "") == "syntax", "real Python bridge returns syntax error")
	GameState.reset_new_game("练功者", "metal")
	GameState.set_current_quest("learn_true_word")
	var first := TechniqueManager.complete_challenge("awakening_word")
	_check(bool(first.first_clear), "true word first clear rewards")
	_check(GameState.current_quest_id == "learn_variables", "true word advances to variables")
	_check(GameState.player.techniques.has("true_word"), "true word technique learned")
	var cultivation_after_first := int(GameState.player.cultivation)
	var repeated := TechniqueManager.complete_challenge("awakening_word")
	_check(not bool(repeated.first_clear) and int(GameState.player.cultivation) == cultivation_after_first, "repeat clear gives no duplicate reward")
	TechniqueManager.complete_challenge("spirit_vessel")
	_check(GameState.current_quest_id == "learn_loops", "variable trial advances to loops")
	TechniqueManager.complete_challenge("cycle_meridian")
	_check(GameState.current_quest_id == "defeat_bug_demon", "loop trial advances to Bug demon")
	_check(GameState.player.techniques.size() == 3, "three techniques learned")
	_check(int(GameState.player.cultivation) == 80, "three technique rewards total 80 cultivation")
	var code_scene: PackedScene = load("res://scenes/ui/CodeChallengePanel.tscn")
	var technique_scene: PackedScene = load("res://scenes/ui/TechniquePanel.tscn")
	_check(code_scene != null and code_scene.can_instantiate(), "CodeEdit challenge panel instantiates")
	_check(technique_scene != null and technique_scene.can_instantiate(), "technique panel instantiates")
	SaveManager.save_path_override = "user://saves/g3_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "G3 state saves")
	GameState.reset_new_game("覆盖", "earth")
	_check(SaveManager.load_game(), "G3 state loads")
	_check(GameState.player.techniques.size() == 3 and GameState.current_quest_id == "defeat_bug_demon", "techniques and quest restore")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	if failures.is_empty():
		print("G3_SMOKE_PASS: isolated Python execution, three techniques, progression and persistence")
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

