import pytest
from pydantic import ValidationError

from psychonavigatorbot.models.test import Questionnaire, TestSummary as SummaryModel


def test_valid_test_summary():
    test = SummaryModel(
        id=1,
        name="Anxiety screening",
        description="Short screening questionnaire",
    )

    assert test.id == 1
    assert test.name == "Anxiety screening"
    assert test.description == "Short screening questionnaire"


def test_valid_questionnaire():
    questionnaire = Questionnaire(
        id=1,
        name="Anxiety screening",
        description="Short screening questionnaire",
        instructions="Choose one answer per question.",
        answer_scale=[{"value": 1, "label": "Never"}],
        questions=[{"id": 1, "text": "Do you feel anxious?"}],
    )

    assert questionnaire.answer_scale[0].value == 1
    assert questionnaire.questions[0].text == "Do you feel anxious?"


def test_missing_required_field():
    with pytest.raises(ValidationError):
        SummaryModel(
            id=1,
            name="Anxiety screening",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "1"),
        ("id", 0),
        ("id", -1),
    ],
)
def test_invalid_type_or_non_positive_id(field, value):
    data = {
        "id": 1,
        "name": "Anxiety screening",
        "description": "Short screening questionnaire",
    }
    data[field] = value

    with pytest.raises(ValidationError):
        SummaryModel.model_validate(data)


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_required_string(value):
    with pytest.raises(ValidationError):
        SummaryModel(
            id=1,
            name=value,
            description="Short screening questionnaire",
        )
