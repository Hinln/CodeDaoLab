extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var creation: Control = load("res://scenes/menu/CharacterCreation.tscn").instantiate()
	add_child(creation)
	_check(creation.get_node("%RootSelect").item_count == 5, "five spirit roots remain available")
	_check(creation.get_node("%IdentitySelect").item_count == 3, "three identity backgrounds are available")
	creation.queue_free()
	GameState.reset_new_game("记名弟子", "water", "artisan")
	_check(str(GameState.player.identity) == "artisan", "identity is stored in player state")
	_check(GameState.identity_name() == "工坊学徒", "identity has a world-facing name")
	_check(GameState.spirit_root_name() == "水", "spirit root has a world-facing name")
	_check(DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan"), "master dialogue starts")
	var first_payload := DialogueManager.current_payload()
	_check(first_payload.has("expression") and first_payload.has("relationship"), "dialogue includes expression and relationship")
	_check(str(first_payload.memory_line).contains("初次相见"), "first meeting creates memory")
	DialogueManager.end_dialogue()
	DialogueManager.start_dialogue("qingxuan_intro", "master_qingxuan")
	var second_payload := DialogueManager.current_payload()
	_check(str(second_payload.memory_line).contains("工坊学徒"), "reunion recalls player identity")
	DialogueManager.end_dialogue()
	GameState.add_affinity("master_qingxuan", 5)
	_check(GameState.relation_stage("master_qingxuan") == "认可", "affinity advances relationship stage")
	var dialogue_scene: PackedScene = load("res://scenes/ui/DialoguePanel.tscn")
	var panel: CanvasLayer = dialogue_scene.instantiate()
	add_child(panel)
	_check(panel.get_node("%NpcPortrait") != null, "dialogue panel contains an animated portrait")
	SaveManager.save_path_override = "user://saves/v02_c_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "identity and memories save")
	GameState.reset_new_game("覆盖", "metal", "academy")
	_check(SaveManager.load_game(), "identity and memories load")
	_check(str(GameState.player.identity) == "artisan" and int(GameState.npc_memory("master_qingxuan").get("meetings", 0)) == 2, "identity and structured memory restore")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	panel.queue_free()
	if failures.is_empty():
		print("V02_C_CHARACTER_NPC_PASS: identity, portraits, expressions, memory and relationships")
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
