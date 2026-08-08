extends Node

var transition_in_progress: bool = false


func goto_scene(path: String) -> void:
	if transition_in_progress:
		return
	transition_in_progress = true
	EventBus.scene_transition_started.emit()
	call_deferred("_change_scene", path)


func _change_scene(path: String) -> void:
	var error := get_tree().change_scene_to_file(path)
	transition_in_progress = false
	if error != OK:
		push_error("无法切换场景 %s：%s" % [path, error_string(error)])
		return
	EventBus.scene_transition_finished.emit()

