from pydantic import BaseModel, Field, ConfigDict


class ApiModel(BaseModel):
    """Базовая модель данных, получаемых от API."""

    model_config = ConfigDict(strict=True, str_strip_whitespace=True)


class Question(ApiModel):
    id: int = Field(ge=1)
    text: str = Field(description="Text of the question.", min_length=1)
    answer_scale: list["AnswerOption"] | None = None


class AnswerOption(ApiModel):
    value: int = Field(ge=1)
    label: str = Field(description="Label of the answer.", min_length=1)


class TestSummary(ApiModel):
    id: int = Field(ge=1, description="ID of the test.")
    name: str = Field(description="Name of the test.", min_length=1)
    description: str = Field(description="Description of the test.", min_length=1)


class Questionnaire(TestSummary):
    instructions: str = Field(description="Instructions of the test.", min_length=1)
    answer_scale: list[AnswerOption] = Field(description="Answer scales of the test.")
    questions: list[Question] = Field(description="Questions of the test.")
