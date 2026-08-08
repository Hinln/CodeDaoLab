extends Node

@onready var title_screen: Control = $TitleScreen
@onready var character_creation: Control = $CharacterCreation
@onready var world_screen: Node2D = $QingyunSect


func _ready() -> void:
	title_screen.new_game_requested.connect(_on_new_game_requested)
	title_screen.continue_requested.connect(_on_continue_requested)
	title_screen.quit_requested.connect(_on_quit_requested)
	character_creation.character_created.connect(_on_character_created)
	character_creation.back_requested.connect(_show_title)
	world_screen.return_title_requested.connect(_show_title)
	title_screen.set_continue_available(SaveManager.has_save())
	_show_only(title_screen)
	print("CodeDaoLab Godot Edition booted with Godot ", Engine.get_version_info().string)


func _on_new_game_requested() -> void:
	character_creation.reset_form()
	_show_only(character_creation)


func _on_continue_requested() -> void:
	if SaveManager.load_game():
		_show_only(world_screen)
		world_screen.enter_world(true)
	else:
		title_screen.show_message("尚无可用存档。")


func _on_quit_requested() -> void:
	get_tree().quit()


func _on_character_created(dao_name: String, spirit_root: String, identity: String) -> void:
	GameState.reset_new_game(dao_name, spirit_root, identity)
	TutorManager.reset_session()
	GameState.set_current_quest("enter_sect")
	_show_only(world_screen)
	world_screen.enter_world(false)


func _show_title() -> void:
	world_screen.leave_world()
	title_screen.set_continue_available(SaveManager.has_save())
	title_screen.show_message("山中无岁月，道途仍在此处等你。")
	_show_only(title_screen)


func _show_only(target: CanvasItem) -> void:
	for screen in [title_screen, character_creation, world_screen]:
		screen.visible = screen == target
