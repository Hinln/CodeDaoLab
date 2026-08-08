extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	_check(FileAccess.file_exists("res://assets/backgrounds/qingyun_title.png"), "generated Qingyun key art exists")
	var art_bytes := FileAccess.get_file_as_bytes("res://assets/backgrounds/qingyun_title.png")
	_check(art_bytes.size() > 100_000, "generated key art is a real raster asset")
	var complete_scene: PackedScene = load("res://scenes/ui/ChapterCompletePanel.tscn")
	_check(complete_scene != null and complete_scene.can_instantiate(), "chapter completion panel instantiates")
	var chapter_nodes: Array = DataRepository.get_data("chapter_01").get("chapter", {}).get("nodes", [])
	_check(chapter_nodes.size() == 8, "chapter one has eight ordered story states")
	GameState.reset_new_game("完整流程", "wood")
	TutorManager.reset_session()
	GameState.set_current_quest("enter_sect")
	DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan")
	DialogueManager.choose(0)
	DialogueManager.choose(0)
	_check(GameState.current_quest_id == "learn_true_word", "playthrough accepts Qingxuan trial")
	var solutions := {
		"awakening_word": "print('天地玄黄，宇宙洪荒。')",
		"spirit_vessel": "qi = 12\nprint(qi)",
		"cycle_meridian": "for i in range(1, 4):\n    print(i)",
	}
	for challenge_id in ["awakening_word", "spirit_vessel", "cycle_meridian"]:
		var response := PythonBridge.execute_sync(challenge_id, solutions[challenge_id], "submit")
		_check(bool(response.get("passed", false)), "%s passes through real Python" % challenge_id)
		TechniqueManager.complete_challenge(challenge_id)
	_check(GameState.current_quest_id == "defeat_bug_demon", "three techniques unlock boss objective")
	var boss: CanvasLayer = load("res://scenes/battle/BugBossArena.tscn").instantiate()
	add_child(boss)
	boss.start_battle()
	var boss_solution := "total = 0\nfor i in range(1, 4):\n    total += i\nprint(total)"
	for challenge_id in ["bug_demon_syntax", "bug_demon_logic", "bug_demon_name"]:
		var response := PythonBridge.execute_sync(challenge_id, boss_solution, "submit")
		_check(bool(response.get("passed", false)), "%s passes through real Python" % challenge_id)
		boss.resolve_result(response, false)
	_check(GameState.current_quest_id == "breakthrough_qi", "boss victory returns player to master")
	DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan")
	DialogueManager.choose(0)
	DialogueManager.choose(0)
	await get_tree().process_frame
	_check(str(GameState.player.realm) == "qi1", "full playthrough reaches qi realm")
	_check(GameState.current_quest_id == "chapter_complete", "full playthrough completes chapter one")
	_check(GameState.player.techniques.size() == 3 and bool(GameState.player.boss_defeated), "full playthrough preserves all milestones")
	_check(int(GameState.player.cultivation) == 230, "full playthrough rewards are balanced and deterministic")
	SaveManager.save_path_override = "user://saves/g6_playthrough.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "full playthrough saves")
	GameState.reset_new_game("覆盖", "metal")
	_check(SaveManager.load_game(), "full playthrough loads")
	_check(GameState.current_quest_id == "chapter_complete" and str(GameState.player.realm) == "qi1", "completed chapter restores")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	boss.queue_free()
	if failures.is_empty():
		print("G6_PLAYTHROUGH_PASS: creation-to-breakthrough chapter loop, generated art and persistence")
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

