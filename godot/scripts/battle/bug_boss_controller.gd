extends CanvasLayer

const STAGES := ["bug_demon_syntax", "bug_demon_logic", "bug_demon_name"]

@onready var overlay: Control = $Overlay
@onready var editor: CodeEdit = %CodeEditor
@onready var visual: Control = %BugDemonVisual
var stage_index: int = 0
var challenge: Dictionary = {}
var pending_action: String = ""
var battle_active: bool = false
var last_result: Dictionary = {}


func _ready() -> void:
	overlay.visible = false
	PythonBridge.challenge_finished.connect(_on_python_result)
	%RunButton.pressed.connect(func() -> void: _execute("run"))
	%AttackButton.pressed.connect(func() -> void: _execute("submit"))
	%TutorButton.pressed.connect(_ask_tutor)
	%RetreatButton.pressed.connect(close_battle)


func start_battle() -> void:
	if bool(GameState.player.get("boss_defeated", false)):
		EventBus.toast_requested.emit("Bug 妖已伏，后山灵雾正在消散。")
		return
	stage_index = 0
	last_result = {}
	battle_active = true
	overlay.visible = true
	GameState.input_locked = true
	visual.set_health(3)
	_load_stage()


func close_battle() -> void:
	if PythonBridge.busy:
		return
	battle_active = false
	overlay.visible = false
	GameState.input_locked = false


func resolve_result(result: Dictionary, penalize_failure: bool = true) -> bool:
	if bool(result.get("passed", false)):
		stage_index += 1
		visual.set_health(3 - stage_index)
		if stage_index >= STAGES.size():
			_finish_victory()
		else:
			%BattleResult.text = "破除一层心魔！下一处错误正在显形。"
			_load_stage()
		return true
	if penalize_failure:
		var mindset := maxi(0, int(GameState.player.get("mindset", 100)) - 5)
		GameState.set_player_value("mindset", mindset)
	return false


func _load_stage() -> void:
	challenge = DataRepository.find_by_id("challenges", "challenges", STAGES[stage_index])
	%StageLabel.text = "心魔 %d / %d" % [stage_index + 1, STAGES.size()]
	%ChallengeTitle.text = str(challenge.title)
	%ChallengePrompt.text = str(challenge.prompt)
	editor.text = str(challenge.starter)
	%OutputLabel.text = "等待法诀运行……"
	%BattleResult.text = "找出错误，运行确认后再发动攻击。"
	%TutorLabel.text = "青玄子传音：心魔最擅长让你只看表象。先运行，再判断是哪一类错误。"
	%RunButton.disabled = false
	%AttackButton.disabled = false


func _execute(action: String) -> void:
	if PythonBridge.busy:
		return
	pending_action = action
	%RunButton.disabled = true
	%AttackButton.disabled = true
	%BattleResult.text = "代码斗法中……"
	if not PythonBridge.request_challenge(str(challenge.id), editor.text, action):
		%BattleResult.text = "无法调动 Python 灵台。"
		%RunButton.disabled = false
		%AttackButton.disabled = false


func _on_python_result(result: Dictionary) -> void:
	if not battle_active or not overlay.visible:
		return
	last_result = result
	var output := str(result.get("stdout", ""))
	var detail := str(result.get("detail", ""))
	%OutputLabel.text = output if not output.is_empty() else (detail if not detail.is_empty() else "（无输出）")
	if pending_action == "submit" and bool(result.get("passed", false)):
		resolve_result(result, false)
		return
	if pending_action == "submit":
		resolve_result(result, true)
		%BattleResult.text = "%s  心境 -5。" % str(result.get("message", "攻击未能破除心魔。"))
	else:
		%BattleResult.text = str(result.get("message", "运行完成。"))
	%RunButton.disabled = false
	%AttackButton.disabled = false


func _ask_tutor() -> void:
	var advice := TutorManager.guidance(str(challenge.get("id", "")), last_result, editor.text)
	%TutorLabel.text = "青玄子传音 · L%d：%s" % [int(advice.get("level", 1)), str(advice.get("text", ""))]


func _finish_victory() -> void:
	var first_clear := QuestManager.complete_bug_demon()
	%ChallengeTitle.text = "Bug 妖伏诛"
	%ChallengePrompt.text = "三处错乱代码尽数归正，后山灵脉重归清明。"
	%BattleResult.text = "修为 +100。返回弟子洞府，请青玄子见证炼气突破。" if first_clear else "心魔已除。"
	%OutputLabel.text = "天地回响：6"
	%RunButton.disabled = true
	%AttackButton.disabled = true
	%RetreatButton.text = "返回青云宗"
