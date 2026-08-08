# -*- coding: utf-8 -*-
"""V0.3-C 功法数据、熟练度、考核与演武场验收。"""

from game import techniques
from game.player import Player


def test_thirteen_data_driven_techniques_cover_required_knowledge():
    all_items = techniques.all_techniques()
    assert len(all_items) >= 12
    titles = {item["title"] for item in all_items}
    assert {"真言诀", "变量吐纳诀", "循环周天诀", "函数凝元术", "列表储物术", "字典观星术", "异常破障诀", "模块引灵术", "文件炼器术", "物华天宝诀"} <= titles


def test_all_technique_solutions_pass_real_validation():
    for technique in techniques.all_techniques():
        challenge = techniques.challenge_for(technique["id"])
        outcome = techniques.validate_challenge(technique["id"], challenge["solution"])
        assert outcome is not None and outcome.passed, technique["id"]


def test_progress_level_and_save_fields_roundtrip():
    player = Player(techniques=["mortal"])
    assert techniques.add_progress(player, "mortal", 60) == 60
    assert techniques.can_exam(player, "mortal") is True
    assert techniques.complete_exam(player, "mortal") == 2
    restored = Player.from_dict(player.to_dict())
    assert restored.technique_progress["mortal"] == 60
    assert restored.technique_level["mortal"] == 2


def test_exam_requires_progress_and_code_validation():
    player = Player(techniques=["mortal"])
    player.technique_level["mortal"] = 1
    assert techniques.can_exam(player, "mortal") is False
    bad = techniques.validate_challenge("mortal", "print('wrong')")
    assert bad is not None and bad.passed is False


def test_task_completion_awards_progress(client, new_player):
    response = client.post("/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"})
    state = response.get_json()["state"]
    assert state["player"]["technique_progress"]["mortal"] == 20


def test_training_ground_api_practice_and_exam(client, new_player):
    client.post("/api/tasks/tutorial_run/submit", json={"code": "print(\"天地玄黄，宇宙洪荒。\")"})
    client.post("/api/breakthrough")
    for location_id in ("library", "mission_hall", "training_ground"):
        assert client.post("/api/world/move", json={"location_id": location_id}).status_code == 200
    challenge = techniques.challenge_for("mortal")
    for _ in range(2):
        response = client.post("/api/techniques/mortal/practice", json={"code": challenge["solution"]})
        assert response.status_code == 200
        assert response.get_json()["outcome"]["passed"] is True
    exam = client.post("/api/techniques/mortal/exam", json={"code": challenge["solution"]})
    assert exam.status_code == 200
    assert exam.get_json()["level"] == 2
