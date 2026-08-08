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
			row.text = "◆ %s · 入门  熟练度 %d/100\n    Python：%s" % [technique.name, technique.progress, technique.knowledge]
			row.add_theme_color_override("font_color", Color("daca91"))
		else:
			row.text = "◇ %s · 尚未习得\n    Python：%s" % [technique.name, technique.knowledge]
			row.add_theme_color_override("font_color", Color("60766e"))
		list.add_child(row)
	overlay.visible = true
	GameState.input_locked = true


func close_panel() -> void:
	overlay.visible = false
	GameState.input_locked = false

