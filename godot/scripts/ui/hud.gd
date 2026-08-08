extends CanvasLayer

signal save_requested
signal return_title_requested

var toast_generation: int = 0


func _ready() -> void:
	%SaveButton.pressed.connect(func() -> void: save_requested.emit())
	%ReturnButton.pressed.connect(func() -> void: return_title_requested.emit())
	%ToastLabel.visible = false


func update_player(player: Dictionary) -> void:
	%DaoNameLabel.text = str(player.get("dao_name", "无名修士"))
	%RealmLabel.text = "境界 · %s" % _realm_name(str(player.get("realm", "mortal")))
	%StatsLabel.text = "修为 %d    悟性 %d    心境 %d" % [
		int(player.get("cultivation", 0)),
		int(player.get("comprehension", 10)),
		int(player.get("mindset", 100)),
	]


func update_quest(title: String, objective: String) -> void:
	%QuestTitle.text = title
	%QuestObjective.text = objective


func set_location(location_name: String) -> void:
	%LocationLabel.text = "青云宗 · %s" % location_name


func set_interaction_prompt(message: String, visible: bool) -> void:
	%InteractionPrompt.text = message
	%InteractionPrompt.visible = visible


func show_toast(message: String) -> void:
	toast_generation += 1
	var generation := toast_generation
	%ToastLabel.text = message
	%ToastLabel.visible = true
	await get_tree().create_timer(2.8).timeout
	if generation == toast_generation:
		%ToastLabel.visible = false


func _realm_name(realm_id: String) -> String:
	return {"mortal": "凡人", "qi1": "炼气一层"}.get(realm_id, realm_id)

