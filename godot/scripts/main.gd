extends Node

@onready var title_screen: Control = $TitleScreen


func _ready() -> void:
	title_screen.new_game_requested.connect(_on_new_game_requested)
	title_screen.continue_requested.connect(_on_continue_requested)
	title_screen.quit_requested.connect(_on_quit_requested)
	title_screen.set_continue_available(SaveManager.has_save())
	print("CodeDaoLab Godot Edition booted with Godot ", Engine.get_version_info().string)


func _on_new_game_requested() -> void:
	GameState.reset_new_game()
	title_screen.show_message("工程骨架已就绪，下一阶段将进入角色创建与青云宗。")


func _on_continue_requested() -> void:
	if SaveManager.load_game():
		title_screen.show_message("已读取青云宗篇存档。")
	else:
		title_screen.show_message("尚无可用存档。")


func _on_quit_requested() -> void:
	get_tree().quit()

