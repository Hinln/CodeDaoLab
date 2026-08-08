extends CanvasLayer

@onready var overlay: Control = $Overlay


func _ready() -> void:
	overlay.visible = false
	EventBus.chapter_completed.connect(open_panel)
	%ContinueButton.pressed.connect(close_panel)


func open_panel(payload: Dictionary) -> void:
	%ChapterTitle.text = "第一章 · %s" % str(payload.get("title", "青云初鸣"))
	%RealmLabel.text = "破境 · %s" % str(payload.get("realm", "炼气一层"))
	%SummaryLabel.text = "你以真代码习得三门功法，修正后山灵脉中的三处错误，并在青玄子见证下踏入炼气。\n\n当前修为 %d · 已习功法 %d / 3" % [int(payload.get("cultivation", 0)), int(payload.get("techniques", 0))]
	overlay.visible = true
	GameState.input_locked = true


func close_panel() -> void:
	overlay.visible = false
	GameState.input_locked = false
	SaveManager.save_game()

