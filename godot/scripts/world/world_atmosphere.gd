extends Node2D

const WEATHER_NAMES := {
	"morning_mist": "清晨薄雾",
	"flowing_clouds": "午后流云",
	"demon_wind": "后山阴风",
	"clear_after_rain": "雨霁青云",
}

var weather_state: String = "morning_mist"
var focus_location: String = "gate"
var phase: float = 0.0
var motes: Array[Dictionary] = []
var audio_player: AudioStreamPlayer
var audio_playback: AudioStreamGeneratorPlayback
var audio_phase: float = 0.0


func _ready() -> void:
	z_index = 4
	_seed_motes()
	_setup_audio()


func _process(delta: float) -> void:
	phase += delta
	_fill_audio()
	queue_redraw()


func set_weather(next_weather: String) -> void:
	if WEATHER_NAMES.has(next_weather):
		weather_state = next_weather


func set_location_focus(location_id: String) -> void:
	focus_location = location_id


func weather_for_quest(quest_id: String) -> String:
	if quest_id == "defeat_bug_demon":
		return "demon_wind"
	if quest_id == "chapter_complete":
		return "clear_after_rain"
	if quest_id in ["learn_true_word", "learn_variables", "learn_loops"]:
		return "flowing_clouds"
	return "morning_mist"


func weather_name() -> String:
	return str(WEATHER_NAMES.get(weather_state, weather_state))


func _seed_motes() -> void:
	var random := RandomNumberGenerator.new()
	random.seed = 20260808
	for index in range(34):
		motes.append({
			"x": random.randf_range(0.0, 1280.0),
			"y": random.randf_range(100.0, 690.0),
			"speed": random.randf_range(5.0, 16.0),
			"size": random.randf_range(1.2, 3.8),
		})


func _setup_audio() -> void:
	var stream := AudioStreamGenerator.new()
	stream.mix_rate = 22050.0
	stream.buffer_length = 0.4
	audio_player = AudioStreamPlayer.new()
	audio_player.name = "ProceduralAmbience"
	audio_player.stream = stream
	audio_player.volume_db = -34.0
	add_child(audio_player)
	if DisplayServer.get_name() == "headless":
		return
	audio_player.play()
	audio_playback = audio_player.get_stream_playback()


func _fill_audio() -> void:
	if audio_playback == null:
		return
	var frequency: float = float({"gate": 110.0, "dormitory": 146.0, "library": 92.0, "training_ground": 174.0, "back_mountain": 73.0}.get(focus_location, 110.0))
	if weather_state == "demon_wind":
		frequency = 61.0
	var frames_to_fill := mini(audio_playback.get_frames_available(), 1024)
	for _frame in range(frames_to_fill):
		audio_phase = fmod(audio_phase + frequency / 22050.0, 1.0)
		var breath := sin(audio_phase * TAU) * 0.018
		var wind := sin(audio_phase * TAU * 0.37 + phase) * (0.014 if weather_state == "demon_wind" else 0.006)
		audio_playback.push_frame(Vector2(breath + wind, breath + wind))


func _draw() -> void:
	var tint: Color = Color({
		"morning_mist": Color(0.55, 0.72, 0.67, 0.065),
		"flowing_clouds": Color(0.78, 0.72, 0.5, 0.045),
		"demon_wind": Color(0.22, 0.08, 0.1, 0.15),
		"clear_after_rain": Color(0.5, 0.84, 0.74, 0.045),
	}.get(weather_state, Color(0.5, 0.7, 0.6, 0.05)))
	draw_rect(Rect2(0, 0, 1280, 720), tint)
	var speed_scale := 2.4 if weather_state == "demon_wind" else 1.0
	for mote in motes:
		var x := fmod(float(mote.x) + phase * float(mote.speed) * speed_scale, 1320.0) - 20.0
		var y := float(mote.y) + sin(phase * 0.8 + float(mote.x)) * 8.0
		var color := Color(0.72, 0.82, 0.67, 0.18)
		if weather_state == "demon_wind":
			color = Color(0.75, 0.27, 0.19, 0.24)
		elif focus_location == "library":
			color = Color(0.9, 0.78, 0.44, 0.22)
		draw_circle(Vector2(x, y), float(mote.size), color)
	if weather_state in ["morning_mist", "demon_wind"]:
		for band in range(4):
			var y := 180.0 + band * 130.0 + sin(phase * 0.22 + band) * 22.0
			var alpha := 0.055 if weather_state == "morning_mist" else 0.075
			draw_line(Vector2(-40, y), Vector2(1320, y - 18), Color(0.72, 0.82, 0.78, alpha), 46.0)
