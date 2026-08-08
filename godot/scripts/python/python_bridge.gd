extends Node

signal challenge_finished(result: Dictionary)

const BRIDGE_DIR := "user://python_bridge"
const RUNNER_PATH := "res://python_bridge/runner.py"

var busy: bool = false
var worker: Thread
var cached_environment: Dictionary = {}


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
	var runner_path := OS.get_executable_path().get_base_dir().path_join("python_bridge/runner.py")
	if not FileAccess.file_exists(runner_path):
		runner_path = ProjectSettings.globalize_path(RUNNER_PATH)
	var exit_code := OS.execute(
		python_executable,
		PackedStringArray([
			runner_path,
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


func check_environment(force: bool = false) -> Dictionary:
	if not force and not cached_environment.is_empty():
		return cached_environment.duplicate(true)
	var output: Array = []
	var python_executable := OS.get_environment("CODEDAO_PYTHON")
	if python_executable.is_empty():
		python_executable = "python"
	var exit_code := OS.execute(python_executable, PackedStringArray(["--version"]), output, true)
	var version_text := "\n".join(output).strip_edges()
	cached_environment = {
		"available": exit_code == 0,
		"executable": python_executable,
		"version": version_text,
		"message": "外部 Python 灵台已连接：%s" % version_text if exit_code == 0 else "未找到 Python 3.10+。代码本身没有出错，请安装 Python 或设置 CODEDAO_PYTHON 后重试。",
	}
	return cached_environment.duplicate(true)


func _internal_error(message: String, detail: String = "") -> Dictionary:
	return {"ok": false, "passed": false, "status": "internal", "message": message, "detail": detail}


func _exit_tree() -> void:
	if worker != null and worker.is_started():
		worker.wait_to_finish()
