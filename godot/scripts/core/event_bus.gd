extends Node

signal player_state_changed(snapshot: Dictionary)
signal quest_changed(quest_id: String)
signal interaction_requested(target_id: String)
signal toast_requested(message: String)
signal code_challenge_requested(challenge_id: String)
signal scene_transition_started
signal scene_transition_finished

