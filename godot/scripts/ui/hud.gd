extends CanvasLayer

signal save_requested
signal return_title_requested

var toast_generation: int = 0
var mentor_generation: int = 0

const BEGINNER_GUIDES := {
	"enter_sect": {
		"title": "第一步 · 前往弟子洞府",
		"progress": "当前目标 1/4：学会移动与交互",
		"body": "使用 WASD 或方向键移动。\n跟随地面发光路径前往左上方的弟子洞府。\n靠近发光目标后按 E，与青玄子交谈。",
	},
	"learn_true_word": {
		"title": "第二步 · 完成首次代码试炼",
		"progress": "当前目标 2/4：让输出与目标完全一致",
		"body": "按 E 打开试炼后，先阅读右侧目标回响。\n文字、顺序、空格和标点都必须一致。\n先点“1 · 运转观阵”，确认后再点“2 · 天地验证”。",
	},
	"learn_loops": {
		"title": "第三步 · 前往演武场",
		"progress": "当前目标 3/4：学习变量、计算与循环",
		"body": "关闭试炼窗口后，跟随灵光前往中央演武场。\n靠近目标按 E。若迷路，请观察右上角的方向和距离提示。",
	},
	"defeat_bug_demon": {
		"title": "第四步 · 修复后山异常",
		"progress": "当前目标 4/4：准备挑战 Bug 妖",
		"body": "完成基础试炼后，前往右下方后山入口。\nBoss 战每一式都先运行观察，再修改代码发动攻击。",
	},
	"chapter_complete": {
		"title": "青云宗篇章已完成",
		"progress": "主线完成：可以自由探索与复习",
		"body": "你已走完整个新手流程。可以重新拜访各地点、打开功法页，或通过存档保留进度。",
	},
}


func _ready() -> void:
	%SaveButton.pressed.connect(func() -> void: save_requested.emit())
	%TechniqueButton.pressed.connect(func() -> void: EventBus.technique_panel_requested.emit())
	%ReturnButton.pressed.connect(func() -> void: return_title_requested.emit())
	%HelpButton.pressed.connect(toggle_help)
	%CloseHelpButton.pressed.connect(toggle_help)
	%ToastLabel.visible = false
	%MentorPanel.visible = false
	%HelpPanel.visible = false


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


func set_directional_target_distance(distance: float, reached: bool = false, direction: String = "") -> void:
	if reached:
		%TargetDistance.text = "已抵达目标区域 · 按 E 交互"
	elif direction.is_empty():
		%TargetDistance.text = "距离约 %d 步" % roundi(distance / 8.0)
	else:
		%TargetDistance.text = "目标在%s · 距离约 %d 步" % [direction, roundi(distance / 8.0)]
	%TargetDistance.add_theme_color_override("font_color", Color("e5cf82") if reached else Color("83b6a0"))


func update_beginner_guide(quest_id: String, auto_open: bool = false) -> void:
	var guide: Dictionary = BEGINNER_GUIDES.get(quest_id, BEGINNER_GUIDES["enter_sect"])
	%HelpTitle.text = str(guide.get("title", "修行指引"))
	%HelpProgress.text = str(guide.get("progress", "查看当前目标"))
	%HelpBody.text = str(guide.get("body", "跟随任务灵光继续探索。"))
	if auto_open:
		%HelpPanel.visible = true


func toggle_help() -> void:
	%HelpPanel.visible = not %HelpPanel.visible


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
