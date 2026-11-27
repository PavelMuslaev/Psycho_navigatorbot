import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from aiogram.types import Message

def test_delete_confirmation_and_cancel():
    from psychonavigatorbot.routers.start import manage_saved

    async def run():
        message = Mock(spec=Message)
        message.chat = SimpleNamespace(type="private")
        message.edit_reply_markup = AsyncMock()
        message.edit_text = AsyncMock()
        message.answer = AsyncMock()
        attempt = uuid4()
        cq = SimpleNamespace(message=message, answer=AsyncMock(), from_user=SimpleNamespace(id=42))
        client = AsyncMock()
        client.get_history.return_value = []
        for action in ["remove", "keep", "remove"]:
            cq.data = f"{action}:{attempt}"
            await manage_saved(cq, client)
            client.delete_attempt.assert_not_awaited()
        markup = message.edit_reply_markup.await_args.kwargs["reply_markup"]
        cq.data = markup.inline_keyboard[0][0].callback_data
        await manage_saved(cq, client)
        client.delete_attempt.assert_awaited_once_with(42, attempt)
        client.get_history.assert_awaited_once()
        assert client.get_history.await_args.args == (42,)
        assert "пуста" in message.answer.await_args.args[0]

    asyncio.run(run())
