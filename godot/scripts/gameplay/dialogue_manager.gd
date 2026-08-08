extends Node

var active_dialogue_id: String = ""
var active_npc_id: String = ""
var active_node_id: String = ""
var active_dialogue: Dictionary = {}
var active_node: Dictionary = {}


func start_dialogue(dialogue_id: String, npc_id: String) -> bool:
	var dialogues: Dictionary = DataRepository.get_data("dialogues").get("dialogues", {})
	if not dialogues.has(dialogue_id):
		push_error("未知对话：%s" % dialogue_id)
		return false
	active_dialogue_id = dialogue_id
	active_npc_id = npc_id
	active_dialogue = dialogues[dialogue_id]
	var memory := GameState.npc_memory(npc_id)
	GameState.remember_npc(npc_id, "meetings", int(memory.get("meetings", 0)) + 1)
	GameState.remember_npc(npc_id, "last_quest", GameState.current_quest_id)
	GameState.input_locked = true
	return _enter_node(str(active_dialogue.get("start", "")))


func choose(option_index: int) -> bool:
	var options := _available_options(active_node.get("options", []))
	if option_index < 0 or option_index >= options.size():
		return false
	var option: Dictionary = options[option_index]
	_apply_actions(option.get("actions", []))
	var next_node := str(option.get("next", ""))
	if next_node.is_empty():
		end_dialogue()
		return true
	return _enter_node(next_node)


func end_dialogue() -> void:
	active_dialogue_id = ""
	active_npc_id = ""
	active_node_id = ""
	active_dialogue = {}
	active_node = {}
	GameState.input_locked = false
	EventBus.dialogue_closed.emit()


func current_payload() -> Dictionary:
	if active_node.is_empty():
		return {}
	var options := _available_options(active_node.get("options", []))
	var affinities: Dictionary = GameState.player.get("npc_affinity", {})
	return {
		"npc_id": active_npc_id,
		"speaker": str(active_node.get("speaker", "")),
		"text": str(active_node.get("text", "")),
		"expression": str(active_node.get("expression", _default_expression())),
		"affinity": int(affinities.get(active_npc_id, 0)),
		"relationship": GameState.relation_stage(active_npc_id),
		"memory_line": _memory_line(),
		"options": options.map(func(option: Dictionary) -> Dictionary: return {"text": str(option.get("text", "继续"))}),
	}


func _default_expression() -> String:
	if active_node_id in ["accept_trial", "breakthrough", "chapter_complete"]:
		return "pleased"
	if active_node_id in ["trial_reminder", "variable_trial"]:
		return "stern"
	return "calm"


func _memory_line() -> String:
	var meetings := int(GameState.npc_memory(active_npc_id).get("meetings", 0))
	if meetings <= 1:
		return "初次相见 · %s正在记住你的选择" % str(active_node.get("speaker", "对方"))
	return "重逢记忆 · %s灵根的%s · 当前关系：%s" % [GameState.spirit_root_name(), GameState.identity_name(), GameState.relation_stage(active_npc_id)]


func _enter_node(node_id: String) -> bool:
	var nodes: Dictionary = active_dialogue.get("nodes", {})
	if not nodes.has(node_id):
		end_dialogue()
		return false
	active_node_id = node_id
	active_node = nodes[node_id]
	_apply_actions(active_node.get("actions", []))
	EventBus.dialogue_opened.emit(current_payload())
	return true


func _available_options(source: Array) -> Array:
	var result: Array = []
	for option in source:
		if _requirement_met(option.get("require", {})):
			result.append(option)
	return result


func _requirement_met(requirement: Dictionary) -> bool:
	if requirement.is_empty():
		return true
	if requirement.has("quest") and GameState.current_quest_id != str(requirement.quest):
		return false
	if requirement.has("flag") and not QuestManager.has_flag(str(requirement.flag)):
		return false
	return true


func _apply_actions(actions: Array) -> void:
	for action in actions:
		match str(action.get("type", "")):
			"set_flag":
				QuestManager.set_flag(str(action.get("id", "")), action.get("value", true))
			"set_quest":
				QuestManager.set_current_quest(str(action.get("id", "")))
			"affinity":
				GameState.add_affinity(active_npc_id, int(action.get("amount", 0)))
			"toast":
				EventBus.toast_requested.emit(str(action.get("message", "")))
			"challenge":
				call_deferred("_request_challenge", str(action.get("id", "")))
			"breakthrough":
				QuestManager.complete_breakthrough()
			_:
				push_warning("忽略未知对话动作：%s" % str(action.get("type", "")))


func _request_challenge(challenge_id: String) -> void:
	EventBus.code_challenge_requested.emit(challenge_id)
