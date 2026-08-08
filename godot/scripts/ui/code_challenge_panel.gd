extends CanvasLayer

@onready var overlay: Control = $Overlay
@onready var editor: CodeEdit = %CodeEditor
var challenge: Dictionary = {}
var submit_pending: bool = false
var completed: bool = false
var last_result: Dictionary = {}
var cast_stage: String = "观题"


func _ready() -> void:
	overlay.visible = false
	EventBus.code_challenge_requested.connect(open_challenge)
	PythonBridge.challenge_finished.connect(_on_challenge_finished)
	%RunButton.pressed.connect(func() -> void: _execute("run"))
	%SubmitButton.pressed.connect(func() -> void: _execute("submit"))
	%TutorButton.pressed.connect(_ask_tutor)
	%DiagnoseButton.pressed.connect(_diagnose)
	%CloseButton.pressed.connect(close_panel)
	editor.text_changed.connect(_on_code_changed)


func open_challenge(challenge_id: String) -> void:
	challenge = DataRepository.find_by_id("challenges", "challenges", challenge_id)
	if challenge.is_empty():
		EventBus.toast_requested.emit("未找到代码试炼：%s" % challenge_id)
		return
	completed = false
	submit_pending = false
	last_result = {}
	%ChallengeTitle.text = str(challenge.title)
	%ChallengePrompt.text = str(challenge.prompt)
	editor.text = str(challenge.starter)
	%OutputLabel.text = "在此查看天地回响。"
	%ResultLabel.text = ""
	%TutorLabel.text = "青玄子传音：先运行一次你的代码，再来问我。"
	%RunButton.disabled = false
	%SubmitButton.disabled = false
	%CloseButton.text = "暂离试炼"
	overlay.visible = true
	GameState.active_challenge_id = challenge_id
	GameState.input_locked = true
	_set_cast_stage("观题", "先观天地之题，再以代码落笔。")
	editor.grab_focus.call_deferred()


func close_panel() -> void:
	if PythonBridge.busy:
		return
	overlay.visible = false
	GameState.active_challenge_id = ""
	GameState.input_locked = false


func _execute(action: String) -> void:
	if PythonBridge.busy:
		return
	submit_pending = action == "submit"
	%RunButton.disabled = true
	%SubmitButton.disabled = true
	_set_cast_stage("起式", "符文收束，准备运转真实 Python 灵台……")
	await get_tree().create_timer(0.16).timeout
	if not overlay.visible:
		return
	_set_cast_stage("运转", "灵力正沿代码逐行运转……")
	if not PythonBridge.request_challenge(str(challenge.id), editor.text, action):
		_set_cast_stage("反噬 · 阵基失联", "无法启动 Python 推演，请检查外部灵台。", "internal")
		%RunButton.disabled = false
		%SubmitButton.disabled = false


func _on_challenge_finished(result: Dictionary) -> void:
	if not overlay.visible:
		return
	last_result = result
	var output := str(result.get("stdout", ""))
	var detail := str(result.get("detail", ""))
	%OutputLabel.text = output if not output.is_empty() else (detail if not detail.is_empty() else "（无输出）")
	var feedback := spell_state_for_result(result, submit_pending)
	_set_cast_stage(str(feedback.stage), str(feedback.message), str(feedback.status))
	if submit_pending and bool(result.get("passed", false)):
		var reward := TechniqueManager.complete_challenge(str(challenge.id))
		%ResultLabel.text = "天地验证通过 · %s" % str(reward.message)
		%ResultLabel.add_theme_color_override("font_color", Color("79c99a"))
		completed = true
		%CloseButton.text = "收功返回"
		%RunButton.disabled = true
		%SubmitButton.disabled = true
		return
	%ResultLabel.text += "\n%s" % str(result.get("message", "代码未通过验证。"))
	%ResultLabel.add_theme_color_override("font_color", Color("e08068"))
	%RunButton.disabled = false
	%SubmitButton.disabled = false


func _ask_tutor() -> void:
	var advice := TutorManager.guidance(str(challenge.get("id", "")), last_result, editor.text)
	%TutorLabel.text = "青玄子传音 · L%d\n%s" % [int(advice.get("level", 1)), str(advice.get("text", "静心再看。"))]


func _diagnose() -> void:
	%TutorLabel.text = "青玄子诊断\n%s" % TutorManager.diagnose(last_result)


func _on_code_changed() -> void:
	if overlay.visible and not PythonBridge.busy and cast_stage in ["观题", "落笔", "显化", "反噬 · 符文断裂", "反噬 · 灵力反冲", "反噬 · 阵法冻结", "反噬 · 法术偏移", "反噬 · 阵基失联"]:
		_set_cast_stage("落笔", "墨光随字符凝成法诀，完成后运转周天。")


func spell_state_for_result(result: Dictionary, is_submission: bool) -> Dictionary:
	var status := str(result.get("status", "internal"))
	if bool(result.get("passed", false)):
		return {
			"stage": "命中" if is_submission else "显化",
			"status": status,
			"message": "法诀命中，天地已认可你的答案。" if is_submission else "法术已显化，观察天地回响后再提交验证。",
		}
	match status:
		"syntax":
			return {"stage": "反噬 · 符文断裂", "status": status, "message": "法诀尚未起行，断裂符文已标出语法所在。"}
		"runtime", "memory":
			return {"stage": "反噬 · 灵力反冲", "status": status, "message": "法诀已经运转，但灵力在执行途中反冲。"}
		"timeout":
			return {"stage": "反噬 · 阵法冻结", "status": status, "message": "周天无法结束，阵法已冻结以保护灵台。"}
		"ok":
			return {"stage": "反噬 · 法术偏移", "status": status, "message": "法术能够显化，但落点与目标异象不符。"}
		_:
			return {"stage": "反噬 · 阵基失联", "status": status, "message": "外部 Python 灵台未能响应，请检查环境后重试。"}


func _set_cast_stage(stage: String, message: String, status: String = "") -> void:
	cast_stage = stage
	%CastStageLabel.text = "%s  /  观题 · 落笔 · 起式 · 运转 · 显化" % stage
	%ResultLabel.text = message
	%CastingVisual.set_cast_state(stage, status)
