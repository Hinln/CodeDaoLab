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


func _notify_changed() -> void:
	EventBus.player_state_changed.emit(snapshot())

