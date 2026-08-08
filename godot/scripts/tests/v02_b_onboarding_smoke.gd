extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var locations: Array = DataRepository.get_data("world").get("map", {}).get("locations", [])
	var location_ids := locations.map(func(item: Dictionary) -> String: return str(item.id))
	var chapter_nodes: Array = DataRepository.get_data("chapter_01").get("chapter", {}).get("nodes", [])
	for node in chapter_nodes:
		var target := str(node.get("target_location", ""))
		_check(target.is_empty() or target in location_ids, "%s has a valid world target" % str(node.id))
	var environment := PythonBridge.check_environment(true)
	_check(bool(environment.get("available", false)), "Python environment preflight succeeds")
	_check(str(environment.get("version", "")).contains("Python"), "preflight reports interpreter version")
	GameState.reset_new_game("初入山门", "wood")
	GameState.set_current_quest("enter_sect")
	var world: Node2D = load("res://scenes/world/QingyunSect.tscn").instantiate()
	add_child(world)
	world.enter_world(false)
	_check(world.target_location_id == "dormitory", "first objective points to the master")
	_check(world.hud.get_node("%TargetLabel").text.contains("弟子洞府"), "HUD names the target location")
	world._update_quest("learn_loops")
	_check(world.target_location_id == "training_ground", "quest changes update world guidance")
	world.hud.show_mentor_message("代码即法术", 0.1)
	_check(world.hud.get_node("%MentorPanel").visible, "mentor transmission appears in world")
	world.leave_world()
	world.queue_free()
	if failures.is_empty():
		print("V02_B_ONBOARDING_PASS: world guidance, mentor transmission and Python preflight")
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
