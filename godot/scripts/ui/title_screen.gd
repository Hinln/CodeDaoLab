extends Control

signal new_game_requested
signal continue_requested
signal quit_requested

@onready var continue_button: Button = %ContinueButton
@onready var status_label: Label = %StatusLabel


func _ready() -> void:
	%NewGameButton.pressed.connect(func() -> void: new_game_requested.emit())
	continue_button.pressed.connect(func() -> void: continue_requested.emit())
	%QuitButton.pressed.connect(func() -> void: quit_requested.emit())


func set_continue_available(available: bool) -> void:
	continue_button.disabled = not available
	continue_button.tooltip_text = "读取青云宗篇独立存档" if available else "尚无青云宗篇存档"


func show_message(message: String) -> void:
	status_label.text = message

