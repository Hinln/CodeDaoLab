extends Control

var root_id: String = "wood"
var phase: float = 0.0
var ceremony_progress: float = 0.0


func _process(delta: float) -> void:
	phase += delta
	ceremony_progress = minf(1.0, ceremony_progress + delta * 0.72)
	queue_redraw()


func begin(next_root_id: String, reduced_motion: bool = false) -> void:
	root_id = next_root_id
	ceremony_progress = 1.0 if reduced_motion else 0.0
	queue_redraw()


func _draw() -> void:
	var center := size * Vector2(0.5, 0.5)
	var color := _root_color(root_id)
	for ring in range(3):
		var progress := clampf(ceremony_progress * 1.45 - ring * 0.2, 0.0, 1.0)
		var radius := 24.0 + ring * 18.0
		draw_arc(center, radius, -PI * 0.5, -PI * 0.5 + TAU * progress, 42, Color(color, 0.88 - ring * 0.16), 4.0)
	for index in range(12):
		var angle := TAU * index / 12.0 + phase * 0.18
		var travel := 88.0 * (1.0 - ceremony_progress) + 42.0
		var point := center + Vector2(cos(angle), sin(angle)) * travel
		draw_circle(point, 3.0, Color(color, 0.72))
	draw_circle(center, 9.0 + ceremony_progress * 10.0, Color(color, 0.45 + ceremony_progress * 0.35))


func _root_color(value: String) -> Color:
	return {
		"metal": Color("eee1b9"),
		"wood": Color("72ca91"),
		"water": Color("6aafe0"),
		"fire": Color("f08355"),
		"earth": Color("cba45d"),
	}.get(value, Color("72ca91"))
