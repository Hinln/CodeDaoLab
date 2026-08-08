extends Node

var hint_levels: Dictionary = {}


func reset_session() -> void:
	hint_levels.clear()


func guidance(challenge_id: String, last_result: Dictionary = {}, _code: String = "") -> Dictionary:
	var hints: Dictionary = DataRepository.get_data("tutor_hints").get("hints", {})
	var levels: Array = hints.get(challenge_id, ["先运行代码，观察天地回响，再判断问题属于语法、运行还是结果。"])
	var level := mini(4, int(hint_levels.get(challenge_id, 0)) + 1)
	if int(GameState.player.get("comprehension", 10)) >= 20:
		level = mini(4, level + 1)
	if int(GameState.player.get("mindset", 100)) <= 30:
		level = maxi(3, level)
	if not last_result.is_empty() and str(last_result.get("status", "")) in ["syntax", "runtime", "timeout", "memory"]:
		level = maxi(2, level)
	var challenge_history := _challenge_history(challenge_id)
	if int(challenge_history.get("failures", 0)) >= 3:
		level = maxi(3, level)
	hint_levels[challenge_id] = level
	_record_hint(challenge_id, level)
	var index := mini(level - 1, levels.size() - 1)
	return {"level": level, "mode": ["引导", "提示", "解释", "答案"][level - 1], "text": "%s%s" % [_voice_prefix(challenge_id), str(levels[index])]}


func diagnose(result: Dictionary) -> String:
	if result.is_empty():
		return "尚无运行结果。先运行一次，错误才会显形。"
	var status := str(result.get("status", "internal"))
	match status:
		"syntax":
			var line := int(result.get("error_line", 0))
			return "这是语法错误%s。检查括号、引号、冒号与缩进；解释器尚未真正运行代码。" % ("，位于第 %d 行" % line if line > 0 else "")
		"runtime":
			return "代码已经运行，但触发了 %s。沿报错最后一行检查变量名、类型与运算条件。" % str(result.get("error_class", "运行异常"))
		"timeout":
			return "法诀运行超时。检查循环条件是否永远无法结束，或是否遗漏了计数变化。"
		"memory":
			return "法诀占用的灵力过多。避免无限增长的列表、字符串或递归。"
		"ok":
			if bool(result.get("passed", false)):
				return "运行与试炼要求一致。你已经用结果证明了这段代码。"
			return "代码可以运行，但输出与目标不同。逐字符比较内容、顺序、空格和换行。"
		_:
			return "桥接层未能得到正常结果。确认系统 Python 可用后再试。"


func record_attempt(challenge_id: String, result: Dictionary) -> Dictionary:
	var history: Dictionary = GameState.player.get("tutor_history", {}).duplicate(true)
	if history.is_empty():
		history = {"total_attempts": 0, "total_failures": 0, "total_successes": 0, "challenges": {}}
	history.total_attempts = int(history.get("total_attempts", 0)) + 1
	var challenges: Dictionary = history.get("challenges", {}).duplicate(true)
	var challenge: Dictionary = challenges.get(challenge_id, {}).duplicate(true)
	challenge.attempts = int(challenge.get("attempts", 0)) + 1
	var status := str(result.get("status", "internal"))
	challenge.last_status = status
	var statuses: Dictionary = challenge.get("statuses", {}).duplicate(true)
	statuses[status] = int(statuses.get(status, 0)) + 1
	challenge.statuses = statuses
	if bool(result.get("passed", false)):
		history.total_successes = int(history.get("total_successes", 0)) + 1
		challenge.successes = int(challenge.get("successes", 0)) + 1
		challenge.independent_success = int(challenge.get("hints_used", 0)) == 0
	else:
		history.total_failures = int(history.get("total_failures", 0)) + 1
		challenge.failures = int(challenge.get("failures", 0)) + 1
	challenges[challenge_id] = challenge
	history.challenges = challenges
	GameState.set_player_value("tutor_history", history)
	GameState.remember_npc("master_qingxuan", "last_challenge", challenge_id)
	GameState.remember_npc("master_qingxuan", "last_result", "success" if bool(result.get("passed", false)) else status)
	return challenge.duplicate(true)


func challenge_greeting(challenge_id: String) -> String:
	var history := _challenge_history(challenge_id)
	if int(history.get("attempts", 0)) == 0:
		return "这是你第一次运转此诀。我先不替你落笔，运行一次，让天地告诉我们发生了什么。"
	if int(history.get("successes", 0)) > 0:
		return "这道法诀你曾成功运转。今日再写，试着比上次更清简。"
	return "我记得你已尝试 %d 次。先看上次的%s，我们只解眼前一处。" % [int(history.get("attempts", 0)), _status_name(str(history.get("last_status", "ok")))]


func success_reflection(challenge_id: String) -> String:
	var history := _challenge_history(challenge_id)
	var concept: String = str({
		"awakening_word": "你已证明 print 能让字符串化作天地回响。",
		"spirit_vessel": "你已让变量 qi 真正容纳并释放灵力。",
		"cycle_meridian": "你已用循环完成三次稳定周天。",
		"bug_demon_syntax": "你补全了语法结构，解释器终于能让法诀起行。",
		"bug_demon_logic": "你分清了赋值与累加，逆流已经归正。",
		"bug_demon_name": "你守住变量真名，引用重新指向同一份灵力。",
	}.get(challenge_id, "你用真实运行结果证明了自己的判断。"))
	var independence := "而且没有索取完整答案。" if bool(history.get("independent_success", false)) else "更重要的是，你知道在受阻时如何逐层求证。"
	return "%s%s" % [concept, independence]


func reunion_message() -> String:
	var history: Dictionary = GameState.player.get("tutor_history", {})
	var attempts := int(history.get("total_attempts", 0))
	if attempts == 0:
		return "%s，先不急着证明天赋。写下第一行真言，我们从一次真实回响开始。" % str(GameState.player.get("dao_name", "弟子"))
	return "我记得你已运转法诀 %d 次，经历 %d 次反噬，也有 %d 次亲手让天地回应。" % [attempts, int(history.get("total_failures", 0)), int(history.get("total_successes", 0))]


func chapter_review() -> String:
	var history: Dictionary = GameState.player.get("tutor_history", {})
	return "%s以%s灵根、%s之身完成 %d 次真实推演；%d 次受阻都没有阻断道途。" % [
		str(GameState.player.get("dao_name", "弟子")),
		GameState.spirit_root_name(),
		GameState.identity_name(),
		int(history.get("total_attempts", 0)),
		int(history.get("total_failures", 0)),
	]


func clear_player_history() -> void:
	GameState.set_player_value("tutor_history", {"total_attempts": 0, "total_failures": 0, "total_successes": 0, "challenges": {}})
	reset_session()


func _record_hint(challenge_id: String, level: int) -> void:
	var history: Dictionary = GameState.player.get("tutor_history", {}).duplicate(true)
	if history.is_empty():
		history = {"total_attempts": 0, "total_failures": 0, "total_successes": 0, "challenges": {}}
	var challenges: Dictionary = history.get("challenges", {}).duplicate(true)
	var challenge: Dictionary = challenges.get(challenge_id, {}).duplicate(true)
	challenge.hints_used = int(challenge.get("hints_used", 0)) + 1
	challenge.highest_hint = maxi(int(challenge.get("highest_hint", 0)), level)
	challenges[challenge_id] = challenge
	history.challenges = challenges
	GameState.set_player_value("tutor_history", history)


func _challenge_history(challenge_id: String) -> Dictionary:
	return GameState.player.get("tutor_history", {}).get("challenges", {}).get(challenge_id, {}).duplicate(true)


func _voice_prefix(challenge_id: String) -> String:
	var root := str(GameState.player.get("spirit_root", "wood"))
	if int(GameState.player.get("mindset", 100)) <= 30:
		return "先稳住呼吸，不必与错误争胜。"
	if root == "water":
		return "顺着回响逐层追溯。"
	if root == "fire":
		return "锋芒可用，但先确认落点。"
	if challenge_id.begins_with("bug_demon"):
		return "心魔会夸大表象，守住事实。"
	return "我在这里。"


func _status_name(status: String) -> String:
	return {"syntax": "符文断裂", "runtime": "灵力反冲", "timeout": "阵法冻结", "ok": "法术偏移", "internal": "阵基失联"}.get(status, "天地回响")
