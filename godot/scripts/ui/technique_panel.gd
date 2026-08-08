extends CanvasLayer

@onready var overlay: Control = $Overlay
@onready var list: VBoxContainer = %TechniqueList


func _ready() -> void:
	overlay.visible = false
	EventBus.technique_panel_requested.connect(open_panel)
	%CloseButton.pressed.connect(close_panel)


func open_panel() -> void:
	for child in list.get_children():
		child.queue_free()
	for technique in TechniqueManager.summary():
		var row := Label.new()
		row.custom_minimum_size = Vector2(0, 50)
		row.add_theme_font_size_override("font_size", 17)
		if technique.learned:
			var definition := DataRepository.find_by_id("techniques", "techniques", str(technique.id))
			var nodes: Array = definition.get("nodes", [])
			var node_texts: Array[String] = []
			for index in range(nodes.size()):
				node_texts.append("◆ %s" % str(nodes[index]) if index < int(technique.level) else "◇ %s" % str(nodes[index]))
			var evidence: Array = technique.get("evidence", [])
			row.text = "%s · %s  阵纹 %d/100\n%s\n证悟：%s · 下一步：%s" % [technique.name, technique.rank, technique.progress, "  ".join(node_texts), str(evidence[-1]) if not evidence.is_empty() else "尚无", technique.next_goal]
			row.add_theme_color_override("font_color", Color("daca91"))
		else:
			row.text = "◇ %s · 尚未习得\nPython：%s · 下一步：%s" % [technique.name, technique.knowledge, technique.next_goal]
			row.add_theme_color_override("font_color", Color("60766e"))
		list.add_child(row)
	overlay.visible = true
	GameState.input_locked = true


func close_panel() -> void:
	overlay.visible = false
	GameState.input_locked = false
