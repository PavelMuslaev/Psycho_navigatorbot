from pydantic import Field

from psychonavigatorbot.models.test import ApiModel


class AnswerSubmission(ApiModel):
    question_id: int = Field(ge=1)
    value: int = Field(ge=1)

class QuestionnaireResultRequest(ApiModel):
    answers: list[AnswerSubmission] = Field(min_length=1)

class FaceScore(ApiModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    score: float = Field(ge=1, le=5)


class DomainScore(ApiModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    score: float = Field(ge=1, le=5)
    facets: list[FaceScore] = Field(min_length=1)


class QuestionnaireResult(ApiModel):
    test_id: int = Field(ge=1)
    domains: list[DomainScore] = Field(min_length=1)



