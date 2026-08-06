from unittest.mock import patch


from psychonavigatorbot.config import get_settings


@patch("psychonavigatorbot.config.getenv")
def test_config(mock_getenv):
    mock_getenv.return_value = "test"

    settings = get_settings()
    assert hasattr(settings, "bot_token")
    assert hasattr(settings, "api_base_url")
    assert settings.api_base_url == "test"
    assert settings.bot_token == "test"
