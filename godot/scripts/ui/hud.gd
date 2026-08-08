extends CanvasLayer

signal save_requested
signal return_title_requested

var toast_generation: int = 0
var mentor_generation: int = 0


func _ready() -> void:
	%SaveButton.pressed.connect(func() -> void: save_requested.emit())
	%TechniqueButton.pressed.connect(func() -> void: EventBus.technique_panel_requested.emit())
	%ReturnButton.pressed.connect(func() -> void: return_title_requested.emit())
	%ToastLabel.visible = false
	%MentorPanel.visible = false


func update_player(player: Dictionary) -> void:
	%DaoNameLabel.text = str(player.get("dao_name", "无名修士"))
	%OriginLabel.text = "%s灵根 · %s" % [GameState.spirit_root_name(), GameState.identity_name()]
	%RealmLabel.text = "境界 · %s" % _realm_name(str(player.get("realm", "mortal")))
	%StatsLabel.text = "修为 %d    悟性 %d    心境 %d" % [
		int(player.get("cultivation", 0)),
		int(player.get("comprehension", 10)),
		int(player.get("mindset", 100)),
	]


func update_quest(title: String, objective: String, target_name: String = "") -> void:
	%QuestTitle.text = title
	%QuestObjective.text = objective
	%TargetLabel.text = "目标地点 · %s" % target_name if not target_name.is_empty() else "目标地点 · 自由探索"
	%TargetDistance.text = ""


func set_target_distance(distance: float, reached: bool = false) -> void:
	%TargetDistance.text = "已抵达目标区域" if reached else "距离约 %d 步" % roundi(distance / 8.0)
	%TargetDistance.add_theme_color_override("font_color", Color("e5cf82") if reached else Color("83b6a0"))


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


func show_mentor_message(message: String, duration: float = 5.0) -> void:
	mentor_generation += 1
	var generation := mentor_generation
	%MentorMessage.text = message
	%MentorPanel.visible = true
	await get_tree().create_timer(duration).timeout
	if generation == mentor_generation:
		%MentorPanel.visible = false


func _realm_name(realm_id: String) -> String:
	return {"mortal": "凡人", "qi1": "炼气一层"}.get(realm_id, realm_id)
