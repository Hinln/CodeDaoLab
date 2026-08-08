extends Node

const SAVE_VERSION := 1
const SAVE_DIR := "user://saves"
const SAVE_PATH := SAVE_DIR + "/chapter_01.json"
var save_path_override: String = ""


func has_save() -> bool:
	return FileAccess.file_exists(_save_path())


func save_game() -> bool:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SAVE_DIR))
	var payload := {
		"version": SAVE_VERSION,
		"player": GameState.snapshot(),
		"meta": {
			"chapter": 1,
			"saved_at": Time.get_datetime_string_from_system(true),
		},
	}
	var save_path := _save_path()
	var temporary_path := save_path + ".tmp"
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		push_error("无法创建临时存档：%s" % FileAccess.get_open_error())
		return false
	file.store_string(JSON.stringify(payload, "  "))
	file.close()
	var target_absolute := ProjectSettings.globalize_path(save_path)
	var temporary_absolute := ProjectSettings.globalize_path(temporary_path)
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(target_absolute)
	var error := DirAccess.rename_absolute(temporary_absolute, target_absolute)
	if error != OK:
		push_error("无法提交存档：%s" % error_string(error))
		return false
	return true


func load_game() -> bool:
	if not has_save():
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(_save_path()))
	if parsed == null or not (parsed is Dictionary):
		push_error("存档格式损坏。")
		return false
	if int(parsed.get("version", 0)) > SAVE_VERSION:
		push_error("存档版本高于当前客户端。")
		return false
	var player_data: Variant = parsed.get("player", {})
	if not (player_data is Dictionary):
		return false
	GameState.apply_snapshot(player_data)
	return true


func remove_save() -> void:
	var save_path := _save_path()
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(save_path))


func _save_path() -> String:
	return save_path_override if not save_path_override.is_empty() else SAVE_PATH
