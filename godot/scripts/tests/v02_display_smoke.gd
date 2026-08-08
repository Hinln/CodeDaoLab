extends Node

var failures: Array[String] = []


func _ready() -> void:
	await get_tree().process_frame
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	var world: Node2D = main.get_node("QingyunSect")
	var camera: Camera2D = world.get_node("Player/Camera2D")
	var hud: CanvasLayer = world.get_node("Hud")
	_check(main.get_node("TitleScreen").visible, "title screen is visible at boot")
	_check(not camera.enabled, "hidden world camera cannot transform the title canvas")
	_check(not hud.visible, "hidden world HUD cannot leak onto the title screen")
	_check(camera.limit_left == 0 and camera.limit_top == 0 and camera.limit_right == 1280 and camera.limit_bottom == 720, "camera is bounded to the 1280x720 world")
	main._on_new_game_requested()
	_check(main.get_node("CharacterCreation").visible and not hud.visible, "character creation remains isolated from world layers")
	main._on_character_created("满屏修士", "wood", "academy")
	_check(world.visible and camera.enabled and hud.visible, "entering the world enables camera and HUD together")
	_check(not main.get_node("TitleScreen").visible and not main.get_node("CharacterCreation").visible, "menu canvases are hidden during play")
	main._show_title()
	_check(not camera.enabled and not hud.visible and main.get_node("TitleScreen").visible, "returning to title disables all world canvas effects")
	main.queue_free()
	if failures.is_empty():
		print("V02_DISPLAY_PASS: camera bounds and screen-layer isolation prevent clipping")
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
