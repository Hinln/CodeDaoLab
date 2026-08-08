extends CharacterBody2D

signal interaction_pressed

@export var move_speed: float = 245.0
@export var movement_bounds := Rect2(70, 105, 1140, 540)
var control_enabled: bool = false

const MOVEMENT_KEYS := {
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"move_up": [KEY_W, KEY_UP],
	"move_down": [KEY_S, KEY_DOWN],
}


func _ready() -> void:
	_ensure_input_actions()
	queue_redraw()


func _physics_process(_delta: float) -> void:
	if not control_enabled or GameState.input_locked:
		velocity = Vector2.ZERO
		return
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction.normalized() * move_speed
	move_and_slide()
	position.x = clampf(position.x, movement_bounds.position.x, movement_bounds.end.x)
	position.y = clampf(position.y, movement_bounds.position.y, movement_bounds.end.y)
	if direction.x != 0.0:
		scale.x = signf(direction.x)


func _ensure_input_actions() -> void:
	for action_value in MOVEMENT_KEYS:
		var action_name := str(action_value)
		if not InputMap.has_action(action_name):
			InputMap.add_action(action_name)
		var keys: Array = MOVEMENT_KEYS[action_value]
		for key_value in keys:
			var keycode := int(key_value)
			if _action_has_key(action_name, keycode):
				continue
			var event := InputEventKey.new()
			if keycode in [KEY_A, KEY_D, KEY_W, KEY_S]:
				event.physical_keycode = keycode
			else:
				event.keycode = keycode
			InputMap.action_add_event(action_name, event)


func _action_has_key(action_name: String, keycode: int) -> bool:
	for event in InputMap.action_get_events(action_name):
		if event is InputEventKey and (event.keycode == keycode or event.physical_keycode == keycode):
			return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if not control_enabled or GameState.input_locked:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_E:
		interaction_pressed.emit()
		get_viewport().set_input_as_handled()


func set_control_enabled(enabled: bool) -> void:
	control_enabled = enabled
	set_physics_process(enabled)


func _draw() -> void:
	_draw_oval(Vector2(0, 19), Vector2(21, 8), Color(0, 0, 0, 0.32))
	draw_polygon(PackedVector2Array([Vector2(-16, 16), Vector2(-11, -14), Vector2(11, -14), Vector2(18, 16)]), PackedColorArray([Color("316b61")]))
	draw_polygon(PackedVector2Array([Vector2(-18, 16), Vector2(0, 7), Vector2(18, 16), Vector2(13, 26), Vector2(-13, 26)]), PackedColorArray([Color("143d3b")]))
	draw_circle(Vector2(0, -22), 11, Color("dfc4a3"))
	draw_arc(Vector2(0, -22), 12, PI, TAU, 16, Color("18282b"), 7)
	draw_line(Vector2(13, -5), Vector2(24, 18), Color("d5b86a"), 3)


func _draw_oval(center: Vector2, radius: Vector2, color: Color) -> void:
	var points := PackedVector2Array()
	for index in range(24):
		var angle := TAU * float(index) / 24.0
		points.append(center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y))
	draw_colored_polygon(points, color)
