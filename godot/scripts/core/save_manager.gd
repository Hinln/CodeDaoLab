extends Node

const SAVE_VERSION := 1
const SAVE_DIR := "user://saves"
const SAVE_PATH := SAVE_DIR + "/chapter_01.json"


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


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
	var temporary_path := SAVE_PATH + ".tmp"
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		push_error("无法创建临时存档：%s" % FileAccess.get_open_error())
		return false
	file.store_string(JSON.stringify(payload, "  "))
	file.close()
	var target_absolute := ProjectSettings.globalize_path(SAVE_PATH)
	var temporary_absolute := ProjectSettings.globalize_path(temporary_path)
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(target_absolute)
	var error := DirAccess.rename_absolute(temporary_absolute, target_absolute)
	if error != OK:
		push_error("无法提交存档：%s" % error_string(error))
		return false
	return true


func load_game() -> bool:
	if not has_save():
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
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

