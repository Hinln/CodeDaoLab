extends CanvasLayer

@onready var overlay: Control = $Overlay
@onready var editor: CodeEdit = %CodeEditor
var challenge: Dictionary = {}
var submit_pending: bool = false
var completed: bool = false
var last_result: Dictionary = {}


func _ready() -> void:
	overlay.visible = false
	EventBus.code_challenge_requested.connect(open_challenge)
	PythonBridge.challenge_finished.connect(_on_challenge_finished)
	%RunButton.pressed.connect(func() -> void: _execute("run"))
	%SubmitButton.pressed.connect(func() -> void: _execute("submit"))
	%TutorButton.pressed.connect(_ask_tutor)
	%DiagnoseButton.pressed.connect(_diagnose)
	%CloseButton.pressed.connect(close_panel)


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
	%ResultLabel.text = "灵台推演中……"
	if not PythonBridge.request_challenge(str(challenge.id), editor.text, action):
		%ResultLabel.text = "无法启动 Python 推演。"
		%RunButton.disabled = false
		%SubmitButton.disabled = false


func _on_challenge_finished(result: Dictionary) -> void:
	if not overlay.visible:
		return
	last_result = result
	var output := str(result.get("stdout", ""))
	var detail := str(result.get("detail", ""))
	%OutputLabel.text = output if not output.is_empty() else (detail if not detail.is_empty() else "（无输出）")
	if submit_pending and bool(result.get("passed", false)):
		var reward := TechniqueManager.complete_challenge(str(challenge.id))
		%ResultLabel.text = "验证通过 · %s" % str(reward.message)
		%ResultLabel.add_theme_color_override("font_color", Color("79c99a"))
		completed = true
		%CloseButton.text = "收功返回"
		%RunButton.disabled = true
		%SubmitButton.disabled = true
		return
	%ResultLabel.text = str(result.get("message", "代码未通过验证。"))
	%ResultLabel.add_theme_color_override("font_color", Color("e08068"))
	%RunButton.disabled = false
	%SubmitButton.disabled = false


func _ask_tutor() -> void:
	var advice := TutorManager.guidance(str(challenge.get("id", "")), last_result, editor.text)
	%TutorLabel.text = "青玄子传音 · L%d\n%s" % [int(advice.get("level", 1)), str(advice.get("text", "静心再看。"))]


func _diagnose() -> void:
	%TutorLabel.text = "青玄子诊断\n%s" % TutorManager.diagnose(last_result)
