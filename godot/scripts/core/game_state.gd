extends Node

const DEFAULT_PLAYER := {
	"dao_name": "",
	"spirit_root": "wood",
	"realm": "mortal",
	"cultivation": 0,
	"comprehension": 10,
	"mindset": 100,
	"position": {"map": "qingyun_sect", "x": 0.0, "y": 0.0},
	"techniques": {},
	"npc_affinity": {},
	"quest_flags": {},
	"boss_defeated": false,
}

var player: Dictionary = DEFAULT_PLAYER.duplicate(true)
var current_quest_id: String = ""
var active_challenge_id: String = ""
var input_locked: bool = false


func reset_new_game(dao_name: String = "", spirit_root: String = "wood") -> void:
	player = DEFAULT_PLAYER.duplicate(true)
	player.dao_name = dao_name.strip_edges()
	player.spirit_root = spirit_root
	current_quest_id = ""
	active_challenge_id = ""
	input_locked = false
	_notify_changed()


func apply_snapshot(snapshot: Dictionary) -> void:
	var restored: Dictionary = DEFAULT_PLAYER.duplicate(true)
	for key in restored:
		if snapshot.has(key):
			restored[key] = snapshot[key]
	player = restored
	current_quest_id = str(snapshot.get("current_quest_id", ""))
	active_challenge_id = ""
	input_locked = false
	_notify_changed()


func snapshot() -> Dictionary:
	var result: Dictionary = player.duplicate(true)
	result.current_quest_id = current_quest_id
	return result


func set_player_value(key: String, value: Variant) -> void:
	player[key] = value
	_notify_changed()


func set_current_quest(quest_id: String) -> void:
	current_quest_id = quest_id
	EventBus.quest_changed.emit(quest_id)
	_notify_changed()


func set_world_position(world_position: Vector2) -> void:
	player.position = {
		"map": "qingyun_sect",
		"x": world_position.x,
		"y": world_position.y,
	}


func add_affinity(npc_id: String, amount: int) -> int:
	var affinities: Dictionary = player.get("npc_affinity", {})
	var updated := clampi(int(affinities.get(npc_id, 0)) + amount, 0, 100)
	affinities[npc_id] = updated
	player.npc_affinity = affinities
	_notify_changed()
	return updated


func set_quest_flag(flag_id: String, value: Variant = true) -> void:
	var flags: Dictionary = player.get("quest_flags", {})
	flags[flag_id] = value
	player.quest_flags = flags
	_notify_changed()


func _notify_changed() -> void:
	EventBus.player_state_changed.emit(snapshot())
