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
	}
	GameState.set_techniques(techniques)
	GameState.add_cultivation(int(effect.cultivation))
	QuestManager.set_flag(str(effect.flag), true)
	QuestManager.set_current_quest(str(effect.next_quest))
	var definition := DataRepository.find_by_id("techniques", "techniques", technique_id)
	techniques_changed.emit(summary())
	return {
		"first_clear": true,
		"technique": str(definition.get("name", technique_id)),
		"cultivation": int(effect.cultivation),
		"message": "习得%s，修为 +%d。" % [definition.get("name", technique_id), int(effect.cultivation)],
	}


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
			"progress": int(state.get("progress", 0)),
		})
	return result

