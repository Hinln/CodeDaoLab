extends CanvasLayer

@onready var overlay: Control = $Overlay


func _ready() -> void:
	overlay.visible = false
	EventBus.chapter_completed.connect(open_panel)
	%ContinueButton.pressed.connect(close_panel)


func open_panel(payload: Dictionary) -> void:
	%ChapterTitle.text = "第一章 · %s" % str(payload.get("title", "青云初鸣"))
	%RealmLabel.text = "破境 · %s" % str(payload.get("realm", "炼气一层"))
	%IdentityLabel.text = "%s · %s灵根 · %s" % [str(GameState.player.get("dao_name", "无名修士")), GameState.spirit_root_name(), GameState.identity_name()]
	%SummaryLabel.text = "你以真代码修正后山灵脉中的三处错误，并在青玄子见证下踏入炼气。当前修为 %d。" % int(payload.get("cultivation", GameState.player.get("cultivation", 0)))
	var technique_lines: Array[String] = []
	for technique in TechniqueManager.summary():
		technique_lines.append("%s · %s · 阵纹 %d/100" % [str(technique.name), str(technique.rank), int(technique.progress)])
	%TechniqueSummary.text = "三诀证悟\n%s" % "    ".join(technique_lines)
	%RelationshipSummary.text = "宗门关系 · 青玄子 %s  /  玄机长老 %s  /  云游子 %s" % [GameState.relation_stage("master_qingxuan"), GameState.relation_stage("elder_library"), GameState.relation_stage("guide_realm")]
	%TutorReview.text = "青玄子评语 · %s" % TutorManager.chapter_review()
	overlay.visible = true
	GameState.input_locked = true
	%ContinueButton.disabled = true
	%ContinueButton.text = "引气入体……"
	var reduced_motion := bool(GameState.player.get("quest_flags", {}).get("reduced_motion", false))
	%BreakthroughVisual.begin(str(GameState.player.get("spirit_root", "wood")), reduced_motion)
	_play_ceremony(reduced_motion)


func close_panel() -> void:
	overlay.visible = false
	GameState.input_locked = false
	SaveManager.save_game()


func _play_ceremony(reduced_motion: bool) -> void:
	if not reduced_motion:
		await get_tree().create_timer(1.4).timeout
	if not overlay.visible:
		return
	%ContinueButton.disabled = false
	%ContinueButton.text = "继续游历青云宗"
