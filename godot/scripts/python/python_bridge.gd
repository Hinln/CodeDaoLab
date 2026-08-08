extends Node

signal challenge_finished(result: Dictionary)

const BRIDGE_DIR := "user://python_bridge"
const RUNNER_PATH := "res://python_bridge/runner.py"

var busy: bool = false
var worker: Thread


func _ready() -> void:
	set_process(false)


func request_challenge(challenge_id: String, code: String, action: String) -> bool:
	if busy:
		return false
	busy = true
	worker = Thread.new()
	var error := worker.start(execute_sync.bind(challenge_id, code, action))
	if error != OK:
		busy = false
		return false
	set_process(true)
	return true


func _process(_delta: float) -> void:
	if not busy or worker == null or worker.is_alive():
		return
	var result: Dictionary = worker.wait_to_finish()
	worker = null
	busy = false
	set_process(false)
	challenge_finished.emit(result)


func execute_sync(challenge_id: String, code: String, action: String = "submit") -> Dictionary:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(BRIDGE_DIR))
	var token := "%s_%s" % [Time.get_ticks_usec(), randi()]
	var request_path := BRIDGE_DIR + "/request_%s.json" % token
	var response_path := BRIDGE_DIR + "/response_%s.json" % token
	var request_file := FileAccess.open(request_path, FileAccess.WRITE)
	if request_file == null:
		return _internal_error("无法创建 Python 请求文件。")
	request_file.store_string(JSON.stringify({
		"challenge_id": challenge_id,
		"code": code,
		"action": action,
	}))
	request_file.close()
	var output: Array = []
	var python_executable := OS.get_environment("CODEDAO_PYTHON")
	if python_executable.is_empty():
		python_executable = "python"
	var exit_code := OS.execute(
		python_executable,
		PackedStringArray([
			ProjectSettings.globalize_path(RUNNER_PATH),
			ProjectSettings.globalize_path(request_path),
			ProjectSettings.globalize_path(response_path),
		]),
		output,
		true
	)
	var result: Dictionary
	if FileAccess.file_exists(response_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(response_path))
		if parsed is Dictionary:
			result = parsed
	if result.is_empty():
		result = _internal_error("Python 进程未返回有效结果。", "\n".join(output) + "\nexit=" + str(exit_code))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(request_path))
	if FileAccess.file_exists(response_path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(response_path))
	return result


func _internal_error(message: String, detail: String = "") -> Dictionary:
	return {"ok": false, "passed": false, "status": "internal", "message": message, "detail": detail}


func _exit_tree() -> void:
	if worker != null and worker.is_started():
		worker.wait_to_finish()

