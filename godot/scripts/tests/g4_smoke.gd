extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var solution := "total = 0\nfor i in range(1, 4):\n    total += i\nprint(total)"
	for challenge_id in ["bug_demon_syntax", "bug_demon_logic", "bug_demon_name"]:
		var response := PythonBridge.execute_sync(challenge_id, solution, "submit")
		_check(bool(response.get("passed", false)), "%s accepts repaired code" % challenge_id)
	var boss_scene: PackedScene = load("res://scenes/battle/BugBossArena.tscn")
	_check(boss_scene != null and boss_scene.can_instantiate(), "Bug boss arena instantiates")
	var boss: CanvasLayer = boss_scene.instantiate()
	add_child(boss)
	GameState.reset_new_game("除魔者", "fire")
	GameState.set_current_quest("defeat_bug_demon")
	GameState.set_techniques({"true_word": {"level": 1}, "variable_breath": {"level": 1}, "cycle_meridian": {"level": 1}})
	boss.start_battle()
	var mindset_before := int(GameState.player.mindset)
	_check(not boss.resolve_result({"passed": false}, true), "failed attack does not advance boss")
	_check(int(GameState.player.mindset) == mindset_before - 5 and boss.stage_index == 0, "failed attack costs mindset only")
	for _stage in range(3):
		_check(boss.resolve_result({"passed": true}, false), "successful attack breaks a boss phase")
	_check(bool(GameState.player.boss_defeated), "three phases defeat Bug demon")
	_check(GameState.current_quest_id == "breakthrough_qi", "boss victory unlocks breakthrough")
	_check(int(GameState.player.cultivation) == 100, "boss first clear grants 100 cultivation")
	_check(not QuestManager.complete_bug_demon() and int(GameState.player.cultivation) == 100, "boss reward cannot repeat")
	_check(DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan"), "breakthrough dialogue starts")
	var opening := DialogueManager.current_payload()
	_check(str(opening.options[0].text).contains("破境"), "breakthrough option is available")
	DialogueManager.choose(0)
	_check(str(GameState.player.realm) == "qi1", "dialogue completes qi breakthrough")
	_check(GameState.current_quest_id == "chapter_complete", "first chapter reaches complete state")
	_check(int(GameState.player.cultivation) == 150, "breakthrough reward added once")
	DialogueManager.choose(0)
	SaveManager.save_path_override = "user://saves/g4_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "completed chapter saves")
	GameState.reset_new_game("覆盖", "water")
	_check(SaveManager.load_game(), "completed chapter loads")
	_check(bool(GameState.player.boss_defeated) and str(GameState.player.realm) == "qi1", "boss and realm state restore")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	boss.queue_free()
	if failures.is_empty():
		print("G4_SMOKE_PASS: three-stage Bug demon, failure penalty, victory, breakthrough and persistence")
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

