class AppError(Exception):
    """Базовое исключение приложения."""

    pass


class ApiClientError(AppError):
    """Базовая ошибка при взаимодействии с API."""

    pass


class ApiUnavailableError(ApiClientError):
    """API недоступно: timeout, ошибка соединения или ответ 5xx."""

    pass


class ApiContractError(ApiClientError):
    """Ответ API не соответствует ожидаемому формату."""

    pass


class QuestionnaireNotFoundError(ApiClientError):
    """Запрошенный тест не найден."""

    def __init__(self, questionnaire_id: id):
        self.questionnaire_id = questionnaire_id
        super().__init__(f"Questionnaire {questionnaire_id} was not found")
