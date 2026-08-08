extends CanvasLayer

@onready var panel: Control = $Overlay
@onready var options_box: VBoxContainer = %OptionsBox


func _ready() -> void:
	panel.visible = false
	EventBus.dialogue_opened.connect(_show_dialogue)
	EventBus.dialogue_closed.connect(_hide_dialogue)


func _show_dialogue(payload: Dictionary) -> void:
	panel.visible = true
	%SpeakerLabel.text = str(payload.get("speaker", ""))
	%AffinityLabel.text = "%s · 好感 %d" % [str(payload.get("relationship", "初识")), int(payload.get("affinity", 0))]
	%DialogueText.text = str(payload.get("text", ""))
	%MemoryLabel.text = str(payload.get("memory_line", ""))
	%NpcPortrait.configure(str(payload.get("npc_id", "")), str(payload.get("expression", "calm")))
	for child in options_box.get_children():
		child.queue_free()
	var options: Array = payload.get("options", [])
	for index in range(options.size()):
		var button := Button.new()
		button.text = str(options[index].get("text", "继续"))
		button.tooltip_text = button.text
		button.custom_minimum_size = Vector2(0, 46)
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.add_theme_font_size_override("font_size", 16)
		button.pressed.connect(func() -> void: DialogueManager.choose(index))
		options_box.add_child(button)
	if options.is_empty():
		var close_button := Button.new()
		close_button.text = "结束对话"
		close_button.pressed.connect(DialogueManager.end_dialogue)
		options_box.add_child(close_button)


func _hide_dialogue() -> void:
	panel.visible = false
