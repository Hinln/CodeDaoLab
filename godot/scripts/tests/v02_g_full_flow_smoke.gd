extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var complete_scene: PackedScene = load("res://scenes/ui/ChapterCompletePanel.tscn")
	var complete_panel: CanvasLayer = complete_scene.instantiate()
	add_child(complete_panel)
	_check(complete_panel.get_node("%BreakthroughVisual") != null, "chapter ending contains breakthrough ceremony")
	GameState.reset_new_game("青岚", "water", "wanderer")
	TutorManager.reset_session()
	_check(str(GameState.player.identity) == "wanderer" and str(GameState.player.spirit_root) == "water", "full flow begins with chosen identity")
	GameState.set_current_quest("enter_sect")
	var world: Node2D = load("res://scenes/world/QingyunSect.tscn").instantiate()
	add_child(world)
	world.enter_world(false)
	_check(world.target_location_id == "dormitory", "opening objective points to the master")
	DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan")
	DialogueManager.choose(0)
	DialogueManager.choose(0)
	_check(GameState.current_quest_id == "learn_true_word", "master trial begins the cultivation path")
	var solutions := {
		"awakening_word": "print('天地玄黄，宇宙洪荒。')",
		"spirit_vessel": "qi = 12\nprint(qi)",
		"cycle_meridian": "for i in range(1, 4):\n    print(i)",
	}
	for challenge_id in ["awakening_word", "spirit_vessel", "cycle_meridian"]:
		var response := PythonBridge.execute_sync(challenge_id, solutions[challenge_id], "submit")
		TutorManager.record_attempt(challenge_id, response)
		_check(bool(response.get("passed", false)), "%s completes as a real spell" % challenge_id)
		TechniqueManager.complete_challenge(challenge_id)
	_check(GameState.current_quest_id == "defeat_bug_demon", "three techniques unlock the Bug demon")
	var world_locations: Array = DataRepository.get_data("world").get("map", {}).get("locations", [])
	world._observe_location(world_locations[0])
	_check(QuestManager.has_flag("observed_gate"), "world discovery persists inside the chapter flow")
	var boss: CanvasLayer = load("res://scenes/battle/BugBossArena.tscn").instantiate()
	add_child(boss)
	boss.start_battle()
	var boss_solution := "total = 0\nfor i in range(1, 4):\n    total += i\nprint(total)"
	for challenge_id in ["bug_demon_syntax", "bug_demon_logic", "bug_demon_name"]:
		var response := PythonBridge.execute_sync(challenge_id, boss_solution, "submit")
		TutorManager.record_attempt(challenge_id, response)
		_check(bool(response.get("passed", false)), "%s is broken by real Python" % challenge_id)
		boss.resolve_result(response, false)
	_check(bool(GameState.player.boss_defeated) and GameState.current_quest_id == "breakthrough_qi", "Boss victory returns the disciple for breakthrough")
	_check(TechniqueManager.summary().all(func(item: Dictionary) -> bool: return item.rank == "运转"), "three techniques reach circulation mastery")
	_check(DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan"), "breakthrough dialogue remains available")
	DialogueManager.choose(0)
	DialogueManager.choose(0)
	await get_tree().process_frame
	_check(str(GameState.player.realm) == "qi1", "disciple reaches qi realm")
	_check(GameState.current_quest_id == "chapter_complete", "first chapter reaches its ending")
	_check(TutorManager.chapter_review().contains("青岚"), "mentor review remembers the disciple")
	complete_panel.open_panel({"title": "青云初鸣", "realm": "炼气一层", "cultivation": GameState.player.cultivation, "techniques": 3})
	_check(complete_panel.get_node("%IdentityLabel").text.contains("山野散修"), "chapter ending reflects identity and root")
	SaveManager.save_path_override = "user://saves/v02_g_full_flow.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "V0.2 full chapter saves")
	GameState.reset_new_game("覆盖", "metal", "academy")
	_check(SaveManager.load_game(), "V0.2 full chapter loads")
	_check(GameState.current_quest_id == "chapter_complete" and str(GameState.player.identity) == "wanderer" and GameState.player.techniques.size() == 3, "identity, mastery and chapter state restore together")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	world.leave_world()
	world.queue_free()
	boss.queue_free()
	complete_panel.queue_free()
	if failures.is_empty():
		print("V02_G_FULL_FLOW_PASS: identity-to-breakthrough journey, ceremony and versioned save")
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
