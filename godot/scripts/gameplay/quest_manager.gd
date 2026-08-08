extends Node


func set_current_quest(quest_id: String) -> void:
	if _quest_node(quest_id).is_empty():
		push_error("未知第一章任务节点：%s" % quest_id)
		return
	GameState.set_current_quest(quest_id)


func set_flag(flag_id: String, value: Variant = true) -> void:
	GameState.set_quest_flag(flag_id, value)


func has_flag(flag_id: String) -> bool:
	return bool(GameState.player.get("quest_flags", {}).get(flag_id, false))


func current_quest() -> Dictionary:
	return _quest_node(GameState.current_quest_id)


func _quest_node(quest_id: String) -> Dictionary:
	var chapter: Dictionary = DataRepository.get_data("chapter_01").get("chapter", {})
	for node in chapter.get("nodes", []):
		if str(node.get("id", "")) == quest_id:
			return node.duplicate(true)
	return {}

