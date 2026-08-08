extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var definitions: Array = DataRepository.get_data("techniques").get("techniques", [])
	_check(definitions.all(func(item: Dictionary) -> bool: return item.get("nodes", []).size() == 3), "every technique has three mastery nodes")
	GameState.reset_new_game("破妄者", "fire", "artisan")
	GameState.set_current_quest("learn_true_word")
	for challenge_id in ["awakening_word", "spirit_vessel", "cycle_meridian"]:
		TechniqueManager.complete_challenge(challenge_id)
	var initial_summary := TechniqueManager.summary()
	_check(initial_summary.all(func(item: Dictionary) -> bool: return item.rank == "入门" and int(item.progress) == 40), "three techniques begin at entry mastery")
	var boss: CanvasLayer = load("res://scenes/battle/BugBossArena.tscn").instantiate()
	add_child(boss)
	boss.start_battle()
	_check(str(boss.get_node("%StageThemeLabel").text).contains("语法"), "first phase presents syntax corruption")
	_check(boss.visual.stage == 0, "boss visual starts as fractured syntax")
	boss.resolve_result({"passed": true}, false)
	_check(boss.visual.stage == 1 and str(boss.get_node("%StageThemeLabel").text).contains("逻辑"), "second phase presents reversed logic flow")
	boss.resolve_result({"passed": true}, false)
	_check(boss.visual.stage == 2 and str(boss.get_node("%StageThemeLabel").text).contains("变量"), "third phase presents stolen variable names")
	boss.resolve_result({"passed": true}, false)
	var final_summary := TechniqueManager.summary()
	_check(final_summary.all(func(item: Dictionary) -> bool: return item.rank == "运转" and int(item.progress) == 75), "boss counters advance all techniques to circulation mastery")
	_check(final_summary.all(func(item: Dictionary) -> bool: return not item.get("evidence", []).is_empty()), "mastery records concrete evidence")
	_check(bool(GameState.player.boss_defeated), "enhanced boss still completes the original objective")
	boss.queue_free()
	if failures.is_empty():
		print("V02_E_TECHNIQUE_BOSS_PASS: mastery nodes and three concept-driven boss phases")
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
