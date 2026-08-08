extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var npcs: Array = DataRepository.get_data("npcs").get("npcs", [])
	var location_ids: Array = DataRepository.get_data("world").get("map", {}).get("locations", []).map(func(item: Dictionary) -> String: return str(item.id))
	_check(npcs.size() == 3, "three core NPCs")
	_check(npcs.all(func(npc: Dictionary) -> bool: return location_ids.has(str(npc.location))), "NPC locations are valid")
	var world: Node2D = load("res://scenes/world/QingyunSect.tscn").instantiate()
	add_child(world)
	await get_tree().process_frame
	_check(world.get_node("NpcActors").get_child_count() == 3, "three NPC actors spawn in world")
	GameState.reset_new_game("问道者", "wood")
	GameState.set_current_quest("enter_sect")
	_check(DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan"), "Qingxuan dialogue starts")
	var opening := DialogueManager.current_payload()
	_check(opening.options.size() == 2, "quest conditions filter dialogue options")
	_check(DialogueManager.choose(0), "accept trial option advances")
	_check(GameState.current_quest_id == "learn_true_word", "dialogue advances first chapter quest")
	_check(QuestManager.has_flag("met_qingxuan"), "dialogue action writes quest flag")
	_check(int(GameState.player.npc_affinity.get("master_qingxuan", 0)) == 5, "dialogue action grants affinity once")
	DialogueManager.choose(0)
	_check(not GameState.input_locked, "dialogue close restores player input")
	SaveManager.save_path_override = "user://saves/g2_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "G2 state saves")
	GameState.reset_new_game("覆盖", "fire")
	_check(SaveManager.load_game(), "G2 state loads")
	_check(GameState.current_quest_id == "learn_true_word", "current quest restores")
	_check(int(GameState.player.npc_affinity.get("master_qingxuan", 0)) == 5, "NPC affinity restores")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	world.queue_free()
	if failures.is_empty():
		print("G2_SMOKE_PASS: NPC actors, conditional dialogue, quest actions and persistence")
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

