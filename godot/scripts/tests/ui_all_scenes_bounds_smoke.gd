extends Node

const VIEWPORT_RECT := Rect2(0, 0, 1280, 720)

var passed := 0
var failed := 0


func _ready() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if condition:
		passed += 1
		print("[PASS] %s" % message)
	else:
		failed += 1
		push_error("[FAIL] %s" % message)


func _inside_viewport(control: Control) -> bool:
	var rect := control.get_global_rect()
	return rect.position.x >= 0.0 and rect.position.y >= 0.0 and rect.end.x <= VIEWPORT_RECT.end.x and rect.end.y <= VIEWPORT_RECT.end.y


func _inside_panel(control: Control, panel: Control) -> bool:
	var rect := control.get_global_rect()
	var panel_rect := panel.get_global_rect()
	return rect.position.x >= panel_rect.position.x and rect.position.y >= panel_rect.position.y and rect.end.x <= panel_rect.end.x and rect.end.y <= panel_rect.end.y


func _stress_text(line_count: int) -> String:
	var lines: Array[String] = []
	for index in range(line_count):
		lines.append("第 %d 行超长提示：观察现象、定位原因、修改代码、再次验证。" % (index + 1))
	return "\n".join(lines)


func _run() -> void:
	GameState.reset_new_game("界面巡检", "wood", "academy")

	var title := preload("res://scenes/menu/TitleScreen.tscn").instantiate()
	add_child(title)
	title.show_message(_stress_text(20))
	await get_tree().process_frame
	var title_panel: Control = title.get_node("Panel")
	var title_status: Control = title.get_node("Panel/Margin/Content/StatusScroll")
	_check(_inside_viewport(title_panel) and _inside_panel(title_status, title_panel), "标题页长状态信息限制在面板滚动区")
	title.queue_free()
	await get_tree().process_frame

	var creation := preload("res://scenes/menu/CharacterCreation.tscn").instantiate()
	add_child(creation)
	await get_tree().process_frame
	var creation_panel: Control = creation.get_node("Panel")
	var creation_buttons: Control = creation.get_node("Panel/Margin/Form/Buttons")
	_check(_inside_viewport(creation_panel) and _inside_panel(creation_buttons, creation_panel), "角色创建操作区完整位于面板内")
	creation.queue_free()
	await get_tree().process_frame

	var hud := preload("res://scenes/ui/Hud.tscn").instantiate()
	add_child(hud)
	hud.update_beginner_guide("enter_sect", true)
	hud.get_node("Root/HelpPanel/HelpMargin/HelpContent/HelpBodyScroll/HelpBody").text = _stress_text(30)
	await get_tree().process_frame
	var help_panel: Control = hud.get_node("Root/HelpPanel")
	var help_close: Control = hud.get_node("Root/HelpPanel/HelpMargin/HelpContent/CloseHelpButton")
	_check(_inside_viewport(help_panel) and _inside_panel(help_close, help_panel), "新手长指引不会挤出关闭按钮")
	hud.get_node("Root/MentorPanel").visible = true
	hud.get_node("Root/MentorPanel/MentorMargin/MentorBox/MentorScroll/MentorMessage").text = _stress_text(20)
	await get_tree().process_frame
	_check(_inside_viewport(hud.get_node("Root/MentorPanel")), "导师长传音限制在 HUD 安全区域")
	hud.queue_free()
	await get_tree().process_frame

	var dialogue := preload("res://scenes/ui/DialoguePanel.tscn").instantiate()
	add_child(dialogue)
	var dialogue_options: Array = []
	for option_index in range(12):
		dialogue_options.append({"text": "第 %d 个较长对话选项：继续询问修行与代码的关系" % (option_index + 1)})
	dialogue._show_dialogue({"speaker": "青玄子", "relationship": "师徒", "affinity": 20, "text": _stress_text(20), "memory_line": _stress_text(8), "npc_id": "master_qingxuan", "expression": "calm", "options": dialogue_options})
	await get_tree().process_frame
	var dialogue_panel: Control = dialogue.get_node("Overlay/Panel")
	var options_scroll: Control = dialogue.get_node("Overlay/Panel/Margin/Content/OptionsScroll")
	_check(_inside_viewport(dialogue_panel) and _inside_panel(options_scroll, dialogue_panel), "长对话与十二个选项保持在滚动面板内")
	dialogue.queue_free()
	await get_tree().process_frame

	var technique := preload("res://scenes/ui/TechniquePanel.tscn").instantiate()
	add_child(technique)
	technique.open_panel()
	var extra_technique := Label.new()
	extra_technique.text = _stress_text(25)
	extra_technique.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	technique.get_node("Overlay/Panel/Margin/Content/TechniqueScroll/TechniqueList").add_child(extra_technique)
	await get_tree().process_frame
	var technique_panel: Control = technique.get_node("Overlay/Panel")
	var technique_close: Control = technique.get_node("Overlay/Panel/Margin/Content/CloseButton")
	_check(_inside_viewport(technique_panel) and _inside_panel(technique_close, technique_panel), "功法长列表不会挤出关闭按钮")
	technique.queue_free()
	await get_tree().process_frame

	var boss := preload("res://scenes/battle/BugBossArena.tscn").instantiate()
	add_child(boss)
	boss.start_battle()
	boss.get_node("Overlay/Panel/Margin/Root/BattleArea/BossSide/BossSideContent/OutputLabel").text = _stress_text(20)
	boss.get_node("Overlay/Panel/Margin/Root/BattleArea/BossSide/BossSideContent/TutorLabel").text = _stress_text(20)
	boss.get_node("Overlay/Panel/Margin/Root/BattleArea/CodeSide/ChallengeBriefScroll/ChallengeBriefContent/ChallengePrompt").text = _stress_text(15)
	boss.get_node("Overlay/Panel/Margin/Root/BattleResultScroll/BattleResult").text = _stress_text(12)
	await get_tree().process_frame
	var boss_panel: Control = boss.get_node("Overlay/Panel")
	var boss_buttons: Control = boss.get_node("Overlay/Panel/Margin/Root/Buttons")
	_check(_inside_viewport(boss_panel) and _inside_panel(boss_buttons, boss_panel), "Boss 超长战报下操作按钮仍完整可见")

	var chapter := preload("res://scenes/ui/ChapterCompletePanel.tscn").instantiate()
	add_child(chapter)
	chapter.open_panel({"title": "青云初鸣", "realm": "炼气一层", "cultivation": 200})
	chapter.get_node("Overlay/Panel/Margin/Content/SummaryScroll/SummaryContent/SummaryLabel").text = _stress_text(20)
	chapter.get_node("Overlay/Panel/Margin/Content/SummaryScroll/SummaryContent/TutorReview").text = _stress_text(30)
	await get_tree().process_frame
	var chapter_panel: Control = chapter.get_node("Overlay/Panel")
	var chapter_continue: Control = chapter.get_node("Overlay/Panel/Margin/Content/ContinueButton")
	_check(_inside_viewport(chapter_panel) and _inside_panel(chapter_continue, chapter_panel), "章节长总结不会挤出继续按钮")

	print("All-scene UI bounds smoke tests: %d passed, %d failed" % [passed, failed])
	get_tree().quit(0 if failed == 0 else 1)
