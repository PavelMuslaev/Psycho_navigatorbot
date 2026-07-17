from src.psychonavigatorbot.config import get_settings

def test_config():
    settings = get_settings()
    assert hasattr(settings, "bot_token")
    assert hasattr(settings, "api_base_url")


