extends Node

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


func _action_has_key(action_name: String, keycode: int) -> bool:
	for event in InputMap.action_get_events(action_name):
		if event is InputEventKey and (event.keycode == keycode or event.physical_keycode == keycode):
			return true
	return false


func _run() -> void:
	GameState.reset_new_game("新手引导", "wood", "academy")
	var world := preload("res://scenes/world/QingyunSect.tscn").instantiate()
	add_child(world)
	world.enter_world(false)
	await get_tree().process_frame

	_check(InputMap.has_action("move_left") and InputMap.has_action("move_right") and InputMap.has_action("move_up") and InputMap.has_action("move_down"), "四个移动动作均已注册")
	_check(_action_has_key("move_left", KEY_A) and _action_has_key("move_left", KEY_LEFT), "A 与左方向键都可左移")
	_check(_action_has_key("move_right", KEY_D) and _action_has_key("move_right", KEY_RIGHT), "D 与右方向键都可右移")
	_check(_action_has_key("move_up", KEY_W) and _action_has_key("move_up", KEY_UP), "W 与上方向键都可上移")
	_check(_action_has_key("move_down", KEY_S) and _action_has_key("move_down", KEY_DOWN), "S 与下方向键都可下移")

	var hud = world.hud
	_check(hud.has_node("Root/HelpPanel"), "HUD 包含独立新手指引面板")
	_check(hud.get_node("Root/HelpPanel").visible, "首次进入青云宗自动打开第一步指引")
	_check("WASD" in hud.get_node("Root/HelpPanel/HelpMargin/HelpContent/HelpBodyScroll/HelpBody").text and "按 E" in hud.get_node("Root/HelpPanel/HelpMargin/HelpContent/HelpBodyScroll/HelpBody").text, "第一步明确说明移动与交互按键")
	hud.set_directional_target_distance(160.0, false, "左上")
	_check("左上" in hud.get_node("Root/QuestPanel/QuestMargin/QuestBox/TargetDistance").text, "任务提示会显示目标方向")

	var panel := preload("res://scenes/ui/CodeChallengePanel.tscn").instantiate()
	add_child(panel)
	panel.open_challenge("awakening_word")
	await get_tree().process_frame
	var guide_label: Label = panel.get_node("Overlay/Panel/Margin/Root/Workspace/OutputPanel/OutputContent/BeginnerGuideLabel")
	_check(guide_label != null, "代码试炼包含分步新手提示")
	var punctuation_feedback: String = panel.beginner_output_feedback({"status": "ok", "passed": false, "stdout": "天地玄黄，宇宙洪荒"})
	_check("句号" in punctuation_feedback and "。" in punctuation_feedback, "首次试炼能精确定位缺少中文句号")
	panel.challenge["expected"] = "灵气 12"
	var generic_feedback: String = panel.beginner_output_feedback({"status": "ok", "passed": false, "stdout": "灵气 11"})
	panel.challenge["expected"] = "1\n2\n3"
	var matching_run: Dictionary = panel.result_for_display({"status": "ok", "passed": false, "stdout": "1  \r\n2\r\n3\r\n"}, false)
	_check("目标" in generic_feedback and "实际" in generic_feedback and bool(matching_run.get("passed", false)) and str(panel.spell_state_for_result(matching_run, false).stage) == "显化", "运行观阵会区分真实差异与已匹配回响")
	for repeat_index in range(40):
		guide_label.text += "\n超长提示第 %d 行：先观察、再修改、最后验证。" % (repeat_index + 1)
	await get_tree().process_frame
	var action_bar: Control = panel.get_node("Overlay/Panel/Margin/Root/Buttons")
	_check(panel.get_node("Overlay/Panel/Margin/Root/Buttons/RunButton").text.begins_with("1") and panel.get_node("Overlay/Panel/Margin/Root/Buttons/SubmitButton").text.begins_with("2") and action_bar.get_global_rect().end.y <= 720.0, "超长提示下操作按钮编号明确且完整位于视口内")

	var boss := preload("res://scenes/battle/BugBossArena.tscn").instantiate()
	add_child(boss)
	_check(boss.has_node("Overlay/Panel/Margin/Root/BattleArea/CodeSide/ChallengeBriefScroll/ChallengeBriefContent/BeginnerBattleGuide"), "Boss 战包含固定破招流程")
	var title := preload("res://scenes/menu/TitleScreen.tscn").instantiate()
	add_child(title)
	_check("v0.2.1" in title.get_node("Version").text, "标题页显示 v0.2.1 版本")

	print("Beginner guidance smoke tests: %d passed, %d failed" % [passed, failed])
	get_tree().quit(0 if failed == 0 else 1)
