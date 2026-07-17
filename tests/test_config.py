from src.psychonavigatorbot.config import get_settings

def test_config():
    settings = get_settings()
    assert settings.bot_token
    assert settings.api_base_url


