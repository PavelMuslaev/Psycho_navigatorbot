from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationError,
    ValidationInfo
)

class Question(BaseModel):
    id: int = Field(ge=1)
    text: str

    @field_validator('text')
    @classmethod
    def non_empty_validator(cls, value: str, info: ValidationInfo):
        if normalized := value.strip():
            raise ValidationError(f"{info.field_name} can not be empty.")
        return normalized

class AnswerOption(BaseModel):
    id: int = Field(ge=1)
    text: str

    @field_validator('text')
    @classmethod
    def non_empty_validator(cls, value: str, info: ValidationInfo):
        if normalized := value.strip():
            raise ValidationError(f"{info.field_name} can not be empty.")
        return normalized



class TestSummary(BaseModel):
    id: int = Field(ge=1, description="ID of the test.")
    name: str = Field(description="Name of the test.")
    description: str = Field(description="Description of the test.")

    @field_validator("name", "description")
    @classmethod
    def validate_non_empty_string(cls, value: str, info: ValidationInfo) -> str:
        if not (normalized := value.strip()):
            raise ValueError(f"{info.field_name} can not be empty.")
        return normalized

class Questionnaire(TestSummary):
    instructions: str = Field(description="Instructions of the test.")
    answer_scale: list[AnswerOption] = Field(description="Answer scales of the test.")
    questions: list[Question] = Field(description="Questions of the test.")

    @field_validator("instructions")
    @classmethod
    def validate_instructions(
            cls,
            value: str,
            info: ValidationInfo,
    ) -> str:
        if not (normalized := value.strip()):
            raise ValueError(f"{info.field_name} can not be empty.")

        return normalized
