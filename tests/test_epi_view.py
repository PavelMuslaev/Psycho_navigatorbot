from psychonavigatorbot.models.test_results import EpiResult
from psychonavigatorbot.views.questionnaire import format_result


def test_epi_result_shows_three_scales():
    result = EpiResult(test_id=2, extraversion=5, neuroticism=24, control=0)
    text = format_result("EPI", result)
    assert "Экстраверсия: 5/24" in text
    assert "Нейротизм: 24/24" in text
    assert "Контрольная шкала: 0/9" in text
