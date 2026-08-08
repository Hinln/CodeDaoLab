extends CanvasLayer

@onready var overlay: Control = $Overlay
@onready var editor: CodeEdit = %CodeEditor
var challenge: Dictionary = {}
var submit_pending: bool = false
var completed: bool = false
var last_result: Dictionary = {}
var cast_stage: String = "观题"

const BEGINNER_GUIDES := {
	"awakening_word": "新手步骤\n1. 阅读上方目标回响。\n2. 检查 print 中的文字与标点。\n3. 点“1 · 运转观阵”查看实际回响。\n4. 完全一致后点“2 · 天地验证”。",
	"spirit_sum": "新手步骤\n1. 找到两个灵气变量。\n2. 用 + 计算总和，不要直接填写答案。\n3. 先运行观察输出，再提交验证。",
	"cycle_meridian": "新手步骤\n1. 观察 range 的起点、终点和步长。\n2. 每次循环输出一次。\n3. 若结果少一项，重点检查 range 的终点。",
}


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
	%TutorLabel.text = "青玄子传音\n%s" % TutorManager.challenge_greeting(challenge_id)
	%BeginnerGuideLabel.text = str(BEGINNER_GUIDES.get(challenge_id, "先读目标，再运行观察；根据诊断修改后提交验证。"))
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
	var evaluated_result := result_for_display(result, submit_pending)
	last_result = evaluated_result
	TutorManager.record_attempt(str(challenge.get("id", "")), evaluated_result)
	var output := str(evaluated_result.get("stdout", ""))
	var detail := str(evaluated_result.get("detail", ""))
	%OutputLabel.text = output if not output.is_empty() else (detail if not detail.is_empty() else "（无输出）")
	var feedback := spell_state_for_result(evaluated_result, submit_pending)
	_set_cast_stage(str(feedback.stage), str(feedback.message), str(feedback.status))
	%BeginnerGuideLabel.text = beginner_output_feedback(evaluated_result)
	if submit_pending and bool(evaluated_result.get("passed", false)):
		var reward := TechniqueManager.complete_challenge(str(challenge.id))
		%ResultLabel.text = "天地验证通过 · %s" % str(reward.message)
		%ResultLabel.add_theme_color_override("font_color", Color("79c99a"))
		%TutorLabel.text = "青玄子 · 见证\n%s" % TutorManager.success_reflection(str(challenge.id))
		completed = true
		%CloseButton.text = "收功返回"
		%RunButton.disabled = true
		%SubmitButton.disabled = true
		return
	if bool(evaluated_result.get("passed", false)):
		%ResultLabel.text += "\n实际回响已经匹配。下一步点击“2 · 天地验证”。"
		%ResultLabel.add_theme_color_override("font_color", Color("79c99a"))
		%TutorLabel.text = "青玄子提醒\n运行只是观阵；回响一致后，还要提交天地验证。"
		%RunButton.disabled = false
		%SubmitButton.disabled = false
		return
	%TutorLabel.text = "青玄子自动诊断\n%s" % TutorManager.diagnose(evaluated_result)
	%ResultLabel.text += "\n%s" % str(evaluated_result.get("message", "代码未通过验证。"))
	%ResultLabel.add_theme_color_override("font_color", Color("e08068"))
	%RunButton.disabled = false
	%SubmitButton.disabled = false


func _ask_tutor() -> void:
	var advice := TutorManager.guidance(str(challenge.get("id", "")), last_result, editor.text)
	%TutorLabel.text = "青玄子传音 · L%d %s\n%s" % [int(advice.get("level", 1)), str(advice.get("mode", "引导")), str(advice.get("text", "静心再看。"))]


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


func result_for_display(result: Dictionary, is_submission: bool) -> Dictionary:
	var evaluated := result.duplicate(true)
	if is_submission or bool(evaluated.get("passed", false)) or str(evaluated.get("status", "internal")) != "ok":
		return evaluated
	var expected := normalize_output(str(challenge.get("expected", "")))
	var actual := normalize_output(str(evaluated.get("stdout", "")))
	if not expected.is_empty() and actual == expected:
		evaluated["passed"] = true
		evaluated["message"] = "运行完成，实际回响与目标一致。"
	return evaluated


func normalize_output(value: String) -> String:
	var normalized := value.replace("\r\n", "\n").replace("\r", "\n").strip_edges()
	var lines: Array[String] = []
	for line in normalized.split("\n", true):
		lines.append(str(line).strip_edges(false, true))
	return "\n".join(lines)


func beginner_output_feedback(result: Dictionary) -> String:
	if bool(result.get("passed", false)):
		return "新手对照：实际回响与目标完全一致，可以继续下一步。"
	var status := str(result.get("status", "internal"))
	if status != "ok":
		return "错误定位：%s" % TutorManager.diagnose(result)
	var expected := normalize_output(str(challenge.get("expected", "")))
	var actual := normalize_output(str(result.get("stdout", "")))
	if actual.is_empty():
		return "差异定位：当前没有任何输出。pass 只会跳过代码，不会产生天地回响。\n请在循环内部添加输出语句，再运行观察。"
	if expected.ends_with("。") and actual == expected.substr(0, expected.length() - 1):
		return "差异定位：你的输出少了最后的中文句号“。”。请在引号内补上它，再次运行。"
	if expected.contains("\n") or actual.contains("\n"):
		var expected_lines := expected.split("\n", false)
		var actual_lines := actual.split("\n", false)
		return "差异定位：回响的行数或数值不匹配。\n目标：%d 行 · %s\n实际：%d 行 · %s" % [expected_lines.size(), " / ".join(expected_lines), actual_lines.size(), " / ".join(actual_lines)]
	if expected.begins_with(actual) and actual.length() < expected.length():
		return "差异定位：实际回响的末尾还缺少“%s”。\n目标：%s\n实际：%s" % [expected.substr(actual.length()), expected, actual]
	return "逐字符对照：文字、顺序、空格和标点都必须一致。\n目标：%s\n实际：%s" % [expected, actual]


func _unhandled_input(event: InputEvent) -> void:
	if not overlay.visible or PythonBridge.busy:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ENTER and event.ctrl_pressed:
		_execute("submit" if event.shift_pressed else "run")
		get_viewport().set_input_as_handled()


func _set_cast_stage(stage: String, message: String, status: String = "") -> void:
	cast_stage = stage
	%CastStageLabel.text = "%s  /  观题 · 落笔 · 起式 · 运转 · 显化" % stage
	%ResultLabel.text = message
	%CastingVisual.set_cast_state(stage, status)
