extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var locations: Array = DataRepository.get_data("world").get("map", {}).get("locations", [])
	_check(locations.size() == 5, "world scope remains five locations")
	_check(locations.all(func(item: Dictionary) -> bool: return not str(item.get("observation", "")).is_empty()), "every location has an observation point")
	_check(locations.all(func(item: Dictionary) -> bool: return not str(item.get("ambience", "")).is_empty()), "every location has an ambience identity")
	GameState.reset_new_game("观息者", "earth", "wanderer")
	GameState.set_current_quest("enter_sect")
	var world: Node2D = load("res://scenes/world/QingyunSect.tscn").instantiate()
	add_child(world)
	world.enter_world(false)
	_check(world.atmosphere.weather_for_quest("defeat_bug_demon") == "demon_wind", "boss objective selects demon wind")
	_check(world.atmosphere.weather_for_quest("chapter_complete") == "clear_after_rain", "chapter completion clears the weather")
	_check(world.atmosphere.get_node("ProceduralAmbience") != null, "procedural ambience player exists")
	var cultivation_before := int(GameState.player.cultivation)
	world._observe_location(locations[0])
	_check(QuestManager.has_flag("observed_gate"), "observation writes a persistent discovery flag")
	_check(int(GameState.player.cultivation) == cultivation_before + 4, "wanderer receives observation insight")
	world._observe_location(locations[0])
	_check(int(GameState.player.cultivation) == cultivation_before + 4, "observation reward cannot repeat")
	world._observe_location(locations[4])
	_check(bool(GameState.npc_memory("guide_realm").get("observed_spirit_vein", false)), "back mountain observation becomes NPC memory")
	world.leave_world()
	world.queue_free()
	if failures.is_empty():
		print("V02_D_WORLD_PASS: five atmospheric locations, weather, sound and discoveries")
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
