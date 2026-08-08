extends Control

signal character_created(dao_name: String, spirit_root: String)
signal back_requested

const ROOTS := [
	{"id": "metal", "name": "金灵根", "desc": "锋锐果决，破障如剑。"},
	{"id": "wood", "name": "木灵根", "desc": "生生不息，悟法绵长。"},
	{"id": "water", "name": "水灵根", "desc": "灵动通透，善察变化。"},
	{"id": "fire", "name": "火灵根", "desc": "炽烈迅捷，敢破心魔。"},
	{"id": "earth", "name": "土灵根", "desc": "厚重守一，道心稳固。"},
]

@onready var dao_name_input: LineEdit = %DaoNameInput
@onready var root_select: OptionButton = %RootSelect
@onready var root_description: Label = %RootDescription
@onready var validation_label: Label = %ValidationLabel


func _ready() -> void:
	for root in ROOTS:
		root_select.add_item(root.name)
	root_select.select(1)
	root_select.item_selected.connect(_on_root_selected)
	%ConfirmButton.pressed.connect(_on_confirm)
	%BackButton.pressed.connect(func() -> void: back_requested.emit())
	_on_root_selected(1)


func reset_form() -> void:
	dao_name_input.text = ""
	root_select.select(1)
	validation_label.text = ""
	_on_root_selected(1)
	dao_name_input.grab_focus.call_deferred()


func _on_root_selected(index: int) -> void:
	root_description.text = ROOTS[index].desc


func _on_confirm() -> void:
	var dao_name := dao_name_input.text.strip_edges()
	if dao_name.length() < 2:
		validation_label.text = "道号至少需要两个字。"
		dao_name_input.grab_focus()
		return
	if dao_name.length() > 12:
		validation_label.text = "道号不可超过十二个字符。"
		return
	validation_label.text = ""
	character_created.emit(dao_name, ROOTS[root_select.selected].id)

