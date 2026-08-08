extends Node

const DATA_FILES := {
	"world": "res://data/world.json",
	"npcs": "res://data/npcs.json",
	"dialogues": "res://data/dialogues.json",
	"techniques": "res://data/techniques.json",
	"challenges": "res://data/challenges.json",
	"chapter_01": "res://data/chapter_01.json",
	"tutor_hints": "res://data/tutor_hints.json",
}

var records: Dictionary = {}
var load_errors: Array[String] = []


func _ready() -> void:
	reload_all()


func reload_all() -> bool:
	records.clear()
	load_errors.clear()
	for key in DATA_FILES:
		var path: String = DATA_FILES[key]
		if not FileAccess.file_exists(path):
			load_errors.append("缺少数据文件：%s" % path)
			continue
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed == null or not (parsed is Dictionary):
			load_errors.append("JSON 数据无效：%s" % path)
			continue
		records[key] = parsed
	for message in load_errors:
		push_error(message)
	return load_errors.is_empty()


func get_data(key: String) -> Dictionary:
	return records.get(key, {}).duplicate(true)


func find_by_id(key: String, collection: String, record_id: String) -> Dictionary:
	var source: Dictionary = records.get(key, {})
	for item in source.get(collection, []):
		if str(item.get("id", "")) == record_id:
			return item.duplicate(true)
	return {}
