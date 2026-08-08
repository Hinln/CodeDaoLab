extends Node

signal techniques_changed(summary: Array)

const CHALLENGE_EFFECTS := {
	"awakening_word": {"technique": "true_word", "progress": 40, "cultivation": 20, "flag": "true_word_complete", "next_quest": "learn_variables"},
	"spirit_vessel": {"technique": "variable_breath", "progress": 40, "cultivation": 25, "flag": "variable_complete", "next_quest": "learn_loops"},
	"cycle_meridian": {"technique": "cycle_meridian", "progress": 40, "cultivation": 35, "flag": "loop_complete", "next_quest": "defeat_bug_demon"},
}


func complete_challenge(challenge_id: String) -> Dictionary:
	if not CHALLENGE_EFFECTS.has(challenge_id):
		return {"first_clear": false, "message": "试炼通过。"}
	var effect: Dictionary = CHALLENGE_EFFECTS[challenge_id]
	if QuestManager.has_flag(str(effect.flag)):
		return {"first_clear": false, "message": "此门功法已通过考校，不再重复结算。"}
	var techniques: Dictionary = GameState.player.get("techniques", {})
	var technique_id := str(effect.technique)
	techniques[technique_id] = {
		"level": 1,
		"progress": int(effect.progress),
		"evidence": ["通过%s真实代码考校" % str(definition_name_for_challenge(challenge_id))],
	}
	GameState.set_techniques(techniques)
	GameState.add_cultivation(int(effect.cultivation))
	QuestManager.set_flag(str(effect.flag), true)
	QuestManager.set_current_quest(str(effect.next_quest))
	var definition := DataRepository.find_by_id("techniques", "techniques", technique_id)
	techniques_changed.emit(summary())
	EventBus.technique_advanced.emit({"technique": str(definition.get("name", technique_id)), "rank": "入门", "message": "功法入门，第一道阵纹已点亮。"})
	return {
		"first_clear": true,
		"technique": str(definition.get("name", technique_id)),
		"cultivation": int(effect.cultivation),
		"message": "习得%s，修为 +%d。" % [definition.get("name", technique_id), int(effect.cultivation)],
	}


func record_usage(technique_id: String, evidence: String, amount: int = 35) -> Dictionary:
	var techniques: Dictionary = GameState.player.get("techniques", {}).duplicate(true)
	if not techniques.has(technique_id):
		return {"advanced": false, "message": "尚未习得对应功法。"}
	var state: Dictionary = techniques[technique_id].duplicate(true)
	var old_level := int(state.get("level", 1))
	state.progress = mini(100, int(state.get("progress", 0)) + amount)
	state.level = 3 if int(state.progress) >= 100 else (2 if int(state.progress) >= 60 else 1)
	var evidence_list: Array = state.get("evidence", []).duplicate()
	if not evidence in evidence_list:
		evidence_list.append(evidence)
	state.evidence = evidence_list
	techniques[technique_id] = state
	GameState.set_techniques(techniques)
	techniques_changed.emit(summary())
	var definition := DataRepository.find_by_id("techniques", "techniques", technique_id)
	var advanced := int(state.level) > old_level
	var payload := {
		"advanced": advanced,
		"technique": str(definition.get("name", technique_id)),
		"rank": rank_name(int(state.level)),
		"progress": int(state.progress),
		"message": "%s提升至%s，阵纹完成度 %d/100。" % [str(definition.get("name", technique_id)), rank_name(int(state.level)), int(state.progress)],
	}
	EventBus.technique_advanced.emit(payload)
	return payload


func rank_name(level: int) -> String:
	return {0: "未习", 1: "入门", 2: "运转", 3: "小成"}.get(level, "入门")


func definition_name_for_challenge(challenge_id: String) -> String:
	return {
		"awakening_word": "真言显化",
		"spirit_vessel": "灵力容纳",
		"cycle_meridian": "周天循环",
	}.get(challenge_id, "代码")


func summary() -> Array:
	var learned: Dictionary = GameState.player.get("techniques", {})
	var result: Array = []
	for definition in DataRepository.get_data("techniques").get("techniques", []):
		var state: Dictionary = learned.get(str(definition.id), {})
		result.append({
			"id": str(definition.id),
			"name": str(definition.name),
			"knowledge": str(definition.knowledge),
			"learned": not state.is_empty(),
			"level": int(state.get("level", 0)),
			"rank": rank_name(int(state.get("level", 0))),
			"progress": int(state.get("progress", 0)),
			"evidence": state.get("evidence", []).duplicate(),
			"next_goal": _next_goal(int(state.get("level", 0))),
		})
	return result


func _next_goal(level: int) -> String:
	return {0: "通过入门考校", 1: "在实战中正确运转", 2: "完成关联心魔领悟", 3: "已达本章上限"}.get(level, "继续参悟")
