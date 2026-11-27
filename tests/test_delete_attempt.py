import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from aiogram.types import Message

from psychonavigatorbot.exceptions.tests import ApiUnavailableError
from psychonavigatorbot.routers.start import manage_saved


@pytest.mark.parametrize(
    ("offset", "remaining", "expected"), [(5, 5, 0), (5, 6, 5), (0, 0, 0)]
)
def test_confirmation_lifecycle(offset, remaining, expected):
    async def run():
        message = Mock(spec=Message)
        message.message_id = 11
        message.chat = SimpleNamespace(type="private")
        message.edit_reply_markup = AsyncMock()
        message.edit_text = AsyncMock()
        attempt = uuid4()
        client = AsyncMock()
        rows = [
            SimpleNamespace(
                attempt_id=uuid4(), test_name="EPI", completed_at=datetime.now(UTC)
            )
            for _ in range(remaining)
        ]
        client.get_history.side_effect = lambda owner, limit, offset: rows[
            offset : offset + limit
        ]

        async def press(data, owner=42):
            cq = SimpleNamespace(
                message=message,
                answer=AsyncMock(),
                from_user=SimpleNamespace(id=owner),
                data=data,
            )
            await manage_saved(cq, client)

        async def open_dialog():
            await press(f"remove:{attempt}:{offset}")
            buttons = message.edit_reply_markup.await_args.kwargs[
                "reply_markup"
            ].inline_keyboard
            return [row[0].callback_data for row in buttons]

        old, cancel = await open_dialog()
        await press(cancel)
        await press(old)
        current, _ = await open_dialog()
        await press(old)
        await press(current, owner=43)
        message.message_id = 12
        await press(current)
        message.message_id = 11
        client.delete_attempt.assert_not_awaited()
        client.delete_attempt.side_effect = ApiUnavailableError("history")
        await press(current)
        client.delete_attempt.assert_awaited_once_with(42, attempt)
        client.delete_attempt.reset_mock(side_effect=True)

        async def delete(owner, attempt_id):
            await asyncio.sleep(0)

        client.delete_attempt.side_effect = delete
        await asyncio.gather(press(current), press(current))
        await press(current)
        client.delete_attempt.assert_awaited_once_with(42, attempt)
        client.get_history.assert_awaited_with(42, limit=6, offset=expected)
        text = message.edit_text.await_args.args[0]
        assert (f"№{expected + 1}" if remaining else "История пока пуста.") in text

    asyncio.run(run())
