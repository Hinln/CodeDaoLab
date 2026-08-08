extends Control

var npc_id: String = "master_qingxuan"
var expression: String = "calm"
var phase: float = 0.0


func _process(delta: float) -> void:
	phase += delta
	queue_redraw()


func configure(next_npc_id: String, next_expression: String) -> void:
	npc_id = next_npc_id
	expression = next_expression
	queue_redraw()


func _draw() -> void:
	var palette := _palette()
	var center := Vector2(size.x * 0.5, size.y * 0.54 + sin(phase * 1.5) * 1.5)
	draw_circle(center + Vector2(0, 64), 74, Color(0, 0, 0, 0.22))
	draw_colored_polygon(PackedVector2Array([
		center + Vector2(-70, 86), center + Vector2(-50, 4), center + Vector2(-25, -8),
		center + Vector2(25, -8), center + Vector2(50, 4), center + Vector2(70, 86),
	]), palette.robe)
	draw_colored_polygon(PackedVector2Array([center + Vector2(-48, 20), center + Vector2(0, 47), center + Vector2(48, 20), center + Vector2(29, 2), center + Vector2(-29, 2)]), palette.trim)
	draw_circle(center + Vector2(0, -43), 38, palette.skin)
	draw_arc(center + Vector2(0, -52), 38, PI, TAU, 28, palette.hair, 17)
	draw_line(center + Vector2(-19, -47), center + Vector2(-7, -47 + _eye_offset()), palette.ink, 3)
	draw_line(center + Vector2(7, -47 + _eye_offset()), center + Vector2(19, -47), palette.ink, 3)
	_draw_mouth(center, palette.ink)
	draw_circle(center + Vector2(0, -96), 7, palette.trim)
	for index in range(5):
		var angle := phase * 0.22 + TAU * index / 5.0
		draw_circle(center + Vector2(cos(angle) * 82, sin(angle) * 38 + 10), 2.4, Color(palette.trim, 0.55))


func _eye_offset() -> float:
	return 3.0 if expression == "pleased" else (-3.0 if expression == "stern" else 0.0)


func _draw_mouth(center: Vector2, color: Color) -> void:
	if expression == "pleased":
		draw_arc(center + Vector2(0, -32), 10, 0.2, PI - 0.2, 12, color, 2)
	elif expression == "question":
		draw_line(center + Vector2(-8, -27), center + Vector2(8, -32), color, 2)
	elif expression == "stern":
		draw_line(center + Vector2(-9, -28), center + Vector2(9, -28), color, 3)
	else:
		draw_arc(center + Vector2(0, -34), 8, 0.25, PI - 0.25, 10, color, 2)


func _palette() -> Dictionary:
	return {
		"master_qingxuan": {"robe": Color("355f56"), "trim": Color("c9b26f"), "hair": Color("dbe0d7"), "skin": Color("d8b99b"), "ink": Color("382e2a")},
		"elder_library": {"robe": Color("66553a"), "trim": Color("d4bd78"), "hair": Color("b8b5a6"), "skin": Color("cda989"), "ink": Color("342a25")},
		"guide_realm": {"robe": Color("405d70"), "trim": Color("8fc0b4"), "hair": Color("27343c"), "skin": Color("d6b796"), "ink": Color("2a2728")},
	}.get(npc_id, {"robe": Color("45665e"), "trim": Color("c9b26f"), "hair": Color("c7ccc4"), "skin": Color("d8b99b"), "ink": Color("382e2a")})
