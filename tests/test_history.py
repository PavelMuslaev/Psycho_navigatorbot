import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from aiogram.types import Message

from psychonavigatorbot.models.test_results import SavedAttempt
from psychonavigatorbot.routers.start import show_history, show_saved
from tests.test_questionnaire_flow import profile


def test_history_screens():
    async def run():
        message = Mock(spec=Message)
        message.chat = SimpleNamespace(type="private")
        message.answer = AsyncMock()
        cq = SimpleNamespace(
            message=message, answer=AsyncMock(), from_user=SimpleNamespace(id=42)
        )
        client = AsyncMock()
        client.get_history.return_value = []
        await show_history(cq, client)
        assert "пуста" in message.answer.await_args.args[0]

        record = SavedAttempt(
            attempt_id=uuid4(),
            completed_at="2026-11-25T10:00:00Z",
            test_name="BFI-2",
            profile=profile(),
        )
        older = record.model_copy(update={"attempt_id": uuid4(), "completed_at": record.completed_at.replace(year=2025)})
        client.get_history.return_value = [record, older]
        client.get_attempt.return_value = record
        await show_history(cq, client)
        client.get_history.assert_awaited_with(42)
        button = message.answer.await_args.kwargs["reply_markup"].inline_keyboard[0][0]
        text = message.answer.await_args.args[0]
        assert "№1 · BFI-2</b>\n25.11.2026 · 10:00 UTC" in text
        assert "№2 · BFI-2</b>\n25.11.2025 · 10:00 UTC" in text
        second = message.answer.await_args.kwargs["reply_markup"].inline_keyboard[1][0]
        assert second.text == "Открыть №2" and second.callback_data == f"saved:{older.attempt_id}"
        assert button.text == "Открыть №1"
        cq.data = button.callback_data
        await show_saved(cq, client)
        client.get_attempt.assert_awaited_once_with(42, record.attempt_id)
        assert "&lt;черта&gt;" in message.answer.await_args.args[0]

    asyncio.run(run())
