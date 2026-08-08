extends Control

var cast_state: String = "观题"
var error_status: String = ""
var phase: float = 0.0
var flash: float = 0.0


func _ready() -> void:
	set_process(true)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(delta: float) -> void:
	phase += delta
	flash = maxf(0.0, flash - delta * 1.8)
	queue_redraw()


func set_cast_state(next_state: String, status: String = "") -> void:
	cast_state = next_state
	error_status = status
	flash = 1.0
	queue_redraw()


func _draw() -> void:
	var center := size * Vector2(0.5, 0.5)
	var root_color := _root_color(str(GameState.player.get("spirit_root", "wood")))
	var danger := cast_state.begins_with("反噬")
	var success := cast_state == "命中"
	var active_color := Color("d9644a") if danger else root_color
	if success:
		active_color = Color("f0d27a")
	var pulse := 1.0 + sin(phase * (5.5 if cast_state == "运转" else 2.4)) * 0.055
	for ring in range(3):
		var radius := (29.0 + ring * 16.0) * pulse
		var alpha := 0.55 - ring * 0.12
		draw_arc(center, radius, phase * (0.35 + ring * 0.22), TAU + phase * 0.2, 40, Color(active_color, alpha), 3.0)
	for index in range(8):
		var angle := TAU * float(index) / 8.0 + phase * 0.12
		var inner := center + Vector2(cos(angle), sin(angle)) * 22.0
		var outer := center + Vector2(cos(angle), sin(angle)) * (45.0 + sin(phase * 2.0 + index) * 4.0)
		draw_line(inner, outer, Color(active_color, 0.68), 2.0)
	if danger:
		_draw_fracture(center, active_color)
	elif success:
		for index in range(12):
			var angle := TAU * float(index) / 12.0 + phase * 0.2
			var point := center + Vector2(cos(angle), sin(angle)) * (58.0 + sin(phase * 3.0 + index) * 8.0)
			draw_circle(point, 2.8, Color(active_color, 0.8))
	draw_circle(center, 10.0 + flash * 6.0, Color(active_color, 0.5 + flash * 0.3))


func _draw_fracture(center: Vector2, color: Color) -> void:
	var skew := 7.0 if error_status == "syntax" else 0.0
	draw_polyline(PackedVector2Array([
		center + Vector2(-47, -28),
		center + Vector2(-13 + skew, -9),
		center + Vector2(-29, 17),
		center + Vector2(4, 6),
		center + Vector2(24, 33),
		center + Vector2(49, 15),
	]), Color(color, 0.95), 4.0)


func _root_color(root_id: String) -> Color:
	return {
		"metal": Color("e8dfc2"),
		"wood": Color("74c49a"),
		"water": Color("68a9d4"),
		"fire": Color("ed8053"),
		"earth": Color("c9a665"),
	}.get(root_id, Color("74c49a"))
