from pydantic import BaseModel, ConfigDict, Field

from psychonavigatorbot.models.test_results import QuestionnaireResultRequest
from psychonavigatorbot.models.test import AnswerOption, Question


class QuestionnaireAttempt(BaseModel):
    model_config = ConfigDict(
        strict=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    test_id: int = Field(ge=1)
    questionnaire_name: str = Field(min_length=1)
    questions: list[Question] = Field(min_length=1)
    answer_scale: list[AnswerOption] = Field(min_length=1)
    current_index: int = Field(default=0, ge=0)
    answer: QuestionnaireResultRequest = Field(default_factory=list)

