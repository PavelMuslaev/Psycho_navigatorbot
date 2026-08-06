class AppError(Exception):
    """Базовое исключение приложения."""

    pass


class ApiClientError(AppError):
    """Базовая ошибка при взаимодействии с API."""

    def __init__(self, url: str, status: int, *, extra_message: str = "") -> None:
        self.url = url
        self.status = status
        self.extra_message = extra_message
        self.message = f"Status code: {self.status}. When contacting the endpoint {self.url}. {self.extra_message}"
        super().__init__(self.message)


class ApiUnavailableError(ApiClientError):
    """API недоступно: timeout, ошибка соединения или ответ 5xx."""

    pass


class ApiContractError(ApiClientError):
    """Ответ API не соответствует ожидаемому формату."""

    pass


class ApiNotFoundError(ApiClientError):
    """Запрашиваемый ресурс не найден"""

    pass
