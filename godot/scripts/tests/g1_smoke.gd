extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	_check(DataRepository.load_errors.is_empty(), "all JSON data loads")
	_check(DataRepository.get_data("world").get("map", {}).get("locations", []).size() == 5, "five Qingyun locations")
	var character_scene: PackedScene = load("res://scenes/menu/CharacterCreation.tscn")
	var world_scene: PackedScene = load("res://scenes/world/QingyunSect.tscn")
	_check(character_scene != null and character_scene.can_instantiate(), "character creation scene instantiates")
	_check(world_scene != null and world_scene.can_instantiate(), "world scene instantiates")
	var world: Node2D = world_scene.instantiate()
	add_child(world)
	GameState.reset_new_game("测试修士", "water")
	GameState.set_current_quest("enter_sect")
	world.enter_world(false)
	await get_tree().process_frame
	var player: CharacterBody2D = world.get_node("Player")
	_check(player.position.distance_to(Vector2(640, 590)) < 1.0, "new player spawns at gate")
	player.position = Vector2(312, 371)
	GameState.set_world_position(player.position)
	SaveManager.save_path_override = "user://saves/g1_smoke.json"
	SaveManager.remove_save()
	_check(SaveManager.save_game(), "save succeeds")
	GameState.reset_new_game("已覆盖", "fire")
	_check(SaveManager.load_game(), "load succeeds")
	_check(str(GameState.player.dao_name) == "测试修士", "dao name restores")
	var restored: Dictionary = GameState.player.position
	_check(Vector2(float(restored.x), float(restored.y)).distance_to(Vector2(312, 371)) < 1.0, "world position restores")
	SaveManager.remove_save()
	SaveManager.save_path_override = ""
	world.queue_free()
	if failures.is_empty():
		print("G1_SMOKE_PASS: character, world, movement foundation and save restore")
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

