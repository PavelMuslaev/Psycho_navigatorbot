from secrets import token_hex

from pydantic import BaseModel, ConfigDict, Field

from psychonavigatorbot.models.test_results import AnswerSubmission
from psychonavigatorbot.models.test import AnswerOption, Question


class QuestionnaireAttempt(BaseModel):
    """Попытка прохождения опросника.

    Хранит снимок опросника на момент старта, текущий прогресс и ответы
    пользователя. Один экземпляр соответствует одной попытке прохождения
    одного опросника одним пользователем.

    Attributes:
        test_id: Идентификатор теста. Должен быть больше или равен 1.
        questionnaire_name: Название опросника. Непустая строка;
            пробелы по краям автоматически удаляются.
        questions: Все вопросы опросника. Должен содержать минимум
            один вопрос.
        answer_scale: Варианты ответа, общие для всех вопросов.
            Должен содержать минимум один вариант.
        current_index: Индекс текущего вопроса в `questions`.
            По умолчанию равен `0`.
        answers: Уже данные пользователем ответы.
            По умолчанию пустой список.
        attempt_id: Идентификатор попытки в виде 8-символьной
            hex-строки. Генерируется автоматически.
        message_id: Идентификатор сообщения Telegram, связанного
            с попыткой. Должен быть больше или равен 1.
        is_complete: `True`, если пользователь ответил на все вопросы.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        strict=True,
        validate_assignment=True,
        # Проверяем даже значения по умолчанию
        validate_default=True,
        str_strip_whitespace=True,
    )

    test_id: int = Field(ge=1, description="Test ID")
    questionnaire_name: str = Field(min_length=1, description="Questionnaire name")

    questions: list[Question] = Field(min_length=1, description="All Questions")
    answer_scale: list[AnswerOption] = Field(min_length=1, description="Answer options")

    current_index: int = Field(default=0, ge=0, description="Index of current question")
    answers: list[AnswerSubmission] = Field(
        default_factory=list,
        description="A list of questions that the user has already answered",
    )

    attempt_id: str = Field(
        default_factory=lambda: token_hex(4),
        pattern="^[a-fA-F0-9]{8}$",
    )
    message_id: int = Field(ge=1)

    @property
    def is_complete(self) -> bool:
        return self.current_index == len(self.questions)
