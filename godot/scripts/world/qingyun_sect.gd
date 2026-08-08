extends Node2D

signal return_title_requested

const MAP_CENTER := Vector2(640, 330)
const INTERACTION_DISTANCE := 92.0
const PATHS := [
	["gate", "dormitory"],
	["gate", "training_ground"],
	["gate", "back_mountain"],
	["dormitory", "training_ground"],
	["training_ground", "library"],
	["training_ground", "back_mountain"],
]

@onready var player: CharacterBody2D = $Player
@onready var hud: CanvasLayer = $Hud
var locations: Array = []
var location_positions: Dictionary = {}
var nearest_location: Dictionary = {}
var world_active: bool = false


func _ready() -> void:
	_load_locations()
	_build_location_labels()
	player.interaction_pressed.connect(_on_interaction_pressed)
	hud.save_requested.connect(_on_save_requested)
	hud.return_title_requested.connect(_on_return_title_requested)
	EventBus.player_state_changed.connect(hud.update_player)
	EventBus.quest_changed.connect(_update_quest)
	set_process(false)
	player.set_control_enabled(false)
	queue_redraw()


func enter_world(restoring: bool) -> void:
	visible = true
	world_active = true
	set_process(true)
	player.set_control_enabled(true)
	var saved_position: Dictionary = GameState.player.get("position", {})
	var target := Vector2(float(saved_position.get("x", 0.0)), float(saved_position.get("y", 0.0)))
	if not restoring or target == Vector2.ZERO:
		target = location_positions.get("gate", Vector2(640, 590))
	player.position = target
	GameState.set_world_position(player.position)
	hud.update_player(GameState.player)
	_update_quest(GameState.current_quest_id)
	hud.show_toast("云阶已尽，%s踏入青云宗。" % str(GameState.player.get("dao_name", "你")))


func leave_world() -> void:
	world_active = false
	set_process(false)
	player.set_control_enabled(false)
	visible = false


func _process(_delta: float) -> void:
	if not world_active:
		return
	GameState.set_world_position(player.position)
	nearest_location = _find_nearest_location()
	if nearest_location.is_empty():
		hud.set_location("云阶山道")
		hud.set_interaction_prompt("", false)
		return
	hud.set_location(str(nearest_location.name))
	hud.set_interaction_prompt("按 E 查看 · %s" % str(nearest_location.name), true)


func _on_interaction_pressed() -> void:
	if nearest_location.is_empty():
		hud.show_toast("附近没有可交互的地点。")
		return
	EventBus.interaction_requested.emit(str(nearest_location.id))
	hud.show_toast("%s\n%s" % [nearest_location.name, nearest_location.description])


func _on_save_requested() -> void:
	GameState.set_world_position(player.position)
	if SaveManager.save_game():
		hud.show_toast("道途已刻入青云玉简。")
	else:
		hud.show_toast("玉简落笔失败，请稍后再试。")


func _on_return_title_requested() -> void:
	GameState.set_world_position(player.position)
	SaveManager.save_game()
	return_title_requested.emit()


func _load_locations() -> void:
	var world_data := DataRepository.get_data("world")
	locations = world_data.get("map", {}).get("locations", [])
	for location in locations:
		location_positions[location.id] = MAP_CENTER + Vector2(float(location.x), float(location.y))


func _build_location_labels() -> void:
	for location in locations:
		var label := Label.new()
		label.text = str(location.name)
		label.position = location_positions[location.id] + Vector2(-72, -74)
		label.size = Vector2(144, 30)
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.add_theme_color_override("font_color", Color("e9dfbd"))
		label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
		label.add_theme_constant_override("shadow_offset_x", 2)
		label.add_theme_constant_override("shadow_offset_y", 2)
		label.add_theme_font_size_override("font_size", 17)
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		$LocationLabels.add_child(label)


func _find_nearest_location() -> Dictionary:
	var result: Dictionary = {}
	var best_distance := INTERACTION_DISTANCE
	for location in locations:
		var distance := player.position.distance_to(location_positions[location.id])
		if distance < best_distance:
			best_distance = distance
			result = location
	return result


func _update_quest(quest_id: String) -> void:
	var chapter: Dictionary = DataRepository.get_data("chapter_01").get("chapter", {})
	for node in chapter.get("nodes", []):
		if str(node.id) == quest_id:
			hud.update_quest(str(node.title), str(node.objective))
			return
	hud.update_quest("自由修行", "探索青云宗，与宗门人物交谈。")


func _draw() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("0b2526"))
	draw_colored_polygon(PackedVector2Array([Vector2(0, 110), Vector2(250, 35), Vector2(470, 130), Vector2(720, 42), Vector2(980, 140), Vector2(1280, 48), Vector2(1280, 0), Vector2(0, 0)]), Color("163c39"))
	draw_colored_polygon(PackedVector2Array([Vector2(0, 170), Vector2(195, 92), Vector2(380, 175), Vector2(590, 98), Vector2(820, 186), Vector2(1080, 90), Vector2(1280, 158), Vector2(1280, 0), Vector2(0, 0)]), Color("102f31"))
	for pair in PATHS:
		if location_positions.has(pair[0]) and location_positions.has(pair[1]):
			draw_line(location_positions[pair[0]], location_positions[pair[1]], Color("49665a"), 28, true)
			draw_line(location_positions[pair[0]], location_positions[pair[1]], Color("8b8c68"), 3, true)
	for location in locations:
		_draw_location(str(location.id), location_positions[location.id])
	for index in range(12):
		var x := 55.0 + index * 109.0
		var y := 625.0 - sin(index * 1.7) * 18.0
		draw_circle(Vector2(x, y), 24, Color("16483d"))
		draw_line(Vector2(x, y + 18), Vector2(x, y + 55), Color("31583f"), 8)


func _draw_location(location_id: String, at: Vector2) -> void:
	_draw_oval(at + Vector2(0, 26), Vector2(58, 17), Color(0, 0, 0, 0.3))
	if location_id == "training_ground":
		draw_circle(at, 47, Color("7d7656"))
		draw_arc(at, 47, 0, TAU, 48, Color("d4bd72"), 3)
		draw_line(at + Vector2(-31, 0), at + Vector2(31, 0), Color("d4bd72"), 2)
		draw_line(at + Vector2(0, -31), at + Vector2(0, 31), Color("d4bd72"), 2)
		return
	if location_id == "back_mountain":
		draw_colored_polygon(PackedVector2Array([at + Vector2(-58, 36), at + Vector2(-17, -48), at + Vector2(12, 7), at + Vector2(43, -55), at + Vector2(72, 36)]), Color("244b43"))
		draw_circle(at + Vector2(28, 4), 23, Color("214d54"))
		return
	draw_rect(Rect2(at + Vector2(-43, -8), Vector2(86, 48)), Color("765743"))
	draw_colored_polygon(PackedVector2Array([at + Vector2(-61, -7), at + Vector2(0, -49), at + Vector2(61, -7)]), Color("244b46"))
	draw_line(at + Vector2(-62, -7), at + Vector2(62, -7), Color("d2b76e"), 4)
	draw_rect(Rect2(at + Vector2(-8, 13), Vector2(16, 27)), Color("1c3030"))


func _draw_oval(center: Vector2, radius: Vector2, color: Color) -> void:
	var points := PackedVector2Array()
	for index in range(32):
		var angle := TAU * float(index) / 32.0
		points.append(center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y))
	draw_colored_polygon(points, color)
