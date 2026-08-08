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
	hint_levels[challenge_id] = level
	var index := mini(level - 1, levels.size() - 1)
	return {"level": level, "text": str(levels[index])}


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

