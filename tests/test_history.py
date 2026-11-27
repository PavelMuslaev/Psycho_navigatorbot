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
            data="history", message=message, answer=AsyncMock(), from_user=SimpleNamespace(id=42)
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
        client.get_history.assert_awaited_with(42, limit=6, offset=0)
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


def test_pages_and_failed_navigation():
    from datetime import UTC, datetime
    from psychonavigatorbot.exceptions.tests import ApiUnavailableError

    async def run():
        rows = [SimpleNamespace(attempt_id=uuid4(), test_name="EPI" if i % 2 else "BFI-2",
                                completed_at=datetime.now(UTC)) for i in range(12)]
        message = Mock(spec=Message)
        message.chat = SimpleNamespace(type="private")
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        cq = SimpleNamespace(message=message, answer=AsyncMock(), from_user=SimpleNamespace(id=42))
        client = AsyncMock()
        client.get_history.side_effect = lambda owner, limit, offset: rows[offset:offset+limit]
        for offset, navigation in [(0, ["Далее"]), (5, ["Назад", "Далее"]), (10, ["Назад"]), (5, ["Назад", "Далее"])]:
            cq.data = f"history:{offset}" if offset else "history"
            await show_history(cq, client)
            sent = message.edit_text if offset else message.answer
            keyboard = sent.await_args.kwargs["reply_markup"].inline_keyboard
            assert [b.text for b in keyboard[-1]] == navigation
            assert [r[0].callback_data for r in keyboard[:-1]] == [
                f"saved:{entry.attempt_id}" + (f":{offset}" if offset else "") for entry in rows[offset:offset+5]]
        message.edit_text.reset_mock()
        client.get_history.side_effect = ApiUnavailableError("history")
        await show_history(cq, client)
        message.edit_text.assert_not_awaited()

    asyncio.run(run())


def test_repeated_stale_next_button():
    from datetime import UTC, datetime
    from aiogram.exceptions import TelegramBadRequest
    from aiogram.methods import EditMessageText
    import pytest

    async def run():
        rows = [SimpleNamespace(attempt_id=uuid4(), test_name="EPI", completed_at=datetime.now(UTC))
                for _ in range(5)]
        message = Mock(spec=Message)
        message.chat = SimpleNamespace(type="private")
        method = EditMessageText(chat_id=42, message_id=1, text="История")
        message.edit_text = AsyncMock(side_effect=[
            None, TelegramBadRequest(method, "Bad Request: message is not modified"),
            TelegramBadRequest(method, "Bad Request: message to edit not found"),
        ])
        cq = SimpleNamespace(message=message, data="history:5", answer=AsyncMock(), from_user=SimpleNamespace(id=42))
        client = AsyncMock()
        client.get_history.side_effect = lambda owner, limit, offset: rows[offset:offset + limit]
        await show_history(cq, client)
        first = message.edit_text.await_args
        buttons = first.kwargs["reply_markup"].inline_keyboard
        assert [row[0].text for row in buttons] == [f"Открыть №{i}" for i in range(1, 6)]
        await show_history(cq, client)
        assert message.edit_text.await_args == first
        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await show_history(cq, client)

    asyncio.run(run())
