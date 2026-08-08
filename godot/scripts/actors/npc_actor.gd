extends Node2D

var npc_data: Dictionary = {}
var robe_color := Color("79a996")


func configure(data: Dictionary) -> void:
	npc_data = data.duplicate(true)
	robe_color = Color(str(npc_data.get("color", "79a996")))
	$NameLabel.text = "%s\n%s" % [npc_data.get("name", "无名修士"), npc_data.get("title", "")]
	queue_redraw()


func _draw() -> void:
	_draw_oval(Vector2(0, 18), Vector2(23, 8), Color(0, 0, 0, 0.3))
	draw_polygon(PackedVector2Array([Vector2(-18, 22), Vector2(-12, -14), Vector2(12, -14), Vector2(18, 22)]), PackedColorArray([robe_color]))
	draw_circle(Vector2(0, -25), 11, Color("d9bea0"))
	draw_arc(Vector2(0, -25), 12, PI, TAU, 16, Color("dce4dd"), 6)
	draw_circle(Vector2(0, -48), 4, Color("d6b86a"))


func _draw_oval(center: Vector2, radius: Vector2, color: Color) -> void:
	var points := PackedVector2Array()
	for index in range(24):
		var angle := TAU * float(index) / 24.0
		points.append(center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y))
	draw_colored_polygon(points, color)

