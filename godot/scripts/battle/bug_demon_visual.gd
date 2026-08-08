extends Control

var health: int = 3
var phase: float = 0.0
var hit_flash: float = 0.0
var stage: int = 0


func _process(delta: float) -> void:
	phase += delta
	hit_flash = maxf(0.0, hit_flash - delta * 2.4)
	queue_redraw()


func set_health(value: int) -> void:
	health = clampi(value, 0, 3)
	hit_flash = 1.0
	queue_redraw()


func set_stage(value: int) -> void:
	stage = clampi(value, 0, 2)
	hit_flash = 0.55
	queue_redraw()


func _draw() -> void:
	var center := size * Vector2(0.5, 0.47)
	var pulse := 1.0 + sin(phase * 3.2) * 0.045
	var core_color := Color("c74b36").lerp(Color("f0c078"), hit_flash)
	for ring in range(4):
		draw_arc(center, (73.0 + ring * 18.0) * pulse, phase * (0.25 + ring * 0.08), TAU + phase * 0.2, 48, Color(0.62, 0.22, 0.13, 0.22 - ring * 0.035), 5.0)
	var body := PackedVector2Array()
	for index in range(12):
		var angle := TAU * float(index) / 12.0
		var radius := 70.0 if index % 2 == 0 else 51.0
		body.append(center + Vector2(cos(angle), sin(angle)) * radius * pulse)
	draw_colored_polygon(body, Color("351d1c").lerp(core_color, hit_flash * 0.45))
	draw_circle(center + Vector2(-23, -8), 9, Color("f3b85f"))
	draw_circle(center + Vector2(23, -8), 9, Color("f3b85f"))
	draw_line(center + Vector2(-28, 29), center + Vector2(0, 16), core_color, 5)
	draw_line(center + Vector2(0, 16), center + Vector2(28, 29), core_color, 5)
	if stage == 0:
		for side in [-1, 1]:
			draw_arc(center + Vector2(side * 88, 0), 27, -PI * 0.48, PI * 0.48, 18, Color("ef8b56"), 5)
			draw_line(center + Vector2(side * 67, -24), center + Vector2(side * 109, -41), Color("ef8b56"), 3)
	elif stage == 1:
		for ring in range(3):
			draw_arc(center, 98 + ring * 14, phase * -1.2, phase * -1.2 + PI * 1.55, 34, Color(0.85, 0.29, 0.2, 0.7 - ring * 0.14), 4)
	else:
		for index in range(7):
			var angle := TAU * index / 7.0 + phase * 0.35
			var shard := center + Vector2(cos(angle), sin(angle)) * 105
			draw_rect(Rect2(shard - Vector2(12, 7), Vector2(24, 14)), Color(0.72, 0.23, 0.2, 0.72))
			draw_line(shard - Vector2(7, 0), shard + Vector2(7, 0), Color("f1b66d"), 2)
	for index in range(3):
		var x := center.x - 76.0 + index * 76.0
		var color := Color("d0523b") if index < health else Color("413637")
		draw_rect(Rect2(Vector2(x, size.y - 45), Vector2(58, 9)), color)
