extends Control

var health: int = 3
var phase: float = 0.0
var hit_flash: float = 0.0


func _process(delta: float) -> void:
	phase += delta
	hit_flash = maxf(0.0, hit_flash - delta * 2.4)
	queue_redraw()


func set_health(value: int) -> void:
	health = clampi(value, 0, 3)
	hit_flash = 1.0
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
	for index in range(3):
		var x := center.x - 76.0 + index * 76.0
		var color := Color("d0523b") if index < health else Color("413637")
		draw_rect(Rect2(Vector2(x, size.y - 45), Vector2(58, 9)), color)

