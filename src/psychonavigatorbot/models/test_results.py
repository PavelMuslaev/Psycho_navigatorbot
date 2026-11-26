from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, BaseModel
from pydantic import Field

from psychonavigatorbot.models.test import ApiModel


class AnswerSubmission(ApiModel):
    question_id: int = Field(ge=1)
    value: int = Field(ge=1)


class QuestionnaireResultRequest(ApiModel):
    answers: list[AnswerSubmission] = Field(min_length=1)


class FacetScore(ApiModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    score: float = Field(ge=1, le=5)


class DomainScore(ApiModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    score: float = Field(ge=1, le=5)
    facets: list[FacetScore] = Field(min_length=3, max_length=3)


class QuestionnaireResult(ApiModel):
    test_id: int = Field(ge=1)
    domains: list[DomainScore] = Field(min_length=5, max_length=5)


class AttemptSummary(BaseModel):
    attempt_id: UUID
    completed_at: AwareDatetime
    test_name: str = Field(min_length=1)


class EpiResult(ApiModel):
    test_id: Literal[2]
    extraversion: int = Field(ge=0, le=24)
    neuroticism: int = Field(ge=0, le=24)
    control: int = Field(ge=0, le=9)


class SavedAttempt(AttemptSummary):
    profile: QuestionnaireResult | EpiResult
