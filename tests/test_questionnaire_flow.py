import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from psychonavigatorbot.callbacks.tests import AnswerCallback, AttemptCallback, TestAction, TestCallback
from psychonavigatorbot.exceptions.tests import ApiUnavailableError
from psychonavigatorbot.models.test import Questionnaire
from psychonavigatorbot.models.test_results import QuestionnaireResult
from psychonavigatorbot.routers.questionnaire import (
    answer_question, cancel_questionnaire, start_questionnaire, submit_result,
)


def profile():
    return {
        "test_id": 1,
        "domains": [
            {"code": code, "name": "<черта>", "score": 3,
             "facets": [{"code": f"{code}{i}", "name": "<аспект>", "score": 3} for i in range(1, 4)]}
            for code in "EACNO"
        ],
    }


@pytest.mark.parametrize("outcome", ["success", "retry", "cancel"])
def test_questionnaire_flow(outcome):
    async def run():
        state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=2, user_id=3))
        message = Mock(spec=Message)
        message.message_id = 11
        message.edit_text = AsyncMock()
        cq = SimpleNamespace(message=message, from_user=SimpleNamespace(id=3), answer=AsyncMock())
        client = AsyncMock()
        questionnaire = Questionnaire(
            id=1, name="<BFI>", instructions="Выберите ответ", description="Тест",
            questions=[{"id": i, "text": f"Пункт {i}"} for i in range(1, 62) if i != 28],
            answer_scale=[{"value": 2, "label": "Редко"}, {"value": 4, "label": "Часто"}],
        )

        async def fetch(test_id):
            cq.answer.assert_awaited_once()
            assert test_id == 1
            return questionnaire

        client.get_questionnaire.side_effect = fetch
        result = QuestionnaireResult.model_validate(profile())
        client.save_result.side_effect = (
            [ApiUnavailableError("api"), result] if outcome == "retry" else [result]
        )
        await start_questionnaire(cq, TestCallback(action=TestAction.START, test_id=1), state, client)
        saved = await state.get_data()
        assert len(saved["questions"]) == 60
        assert "Вопрос 1 из 60" in message.edit_text.await_args.args[0]
        keyboard = message.edit_text.await_args.kwargs["reply_markup"].inline_keyboard
        buttons = [AnswerCallback.unpack(row[0].callback_data) for row in keyboard[:-1]]
        assert [b.value for b in buttons] == [2, 4]
        assert all(len(b.pack().encode()) <= 64 for b in buttons)
        cancel = AttemptCallback.unpack(keyboard[-1][0].callback_data)
        assert cancel.action == TestAction.CANCEL
        if outcome == "cancel":
            await cancel_questionnaire(cq, cancel, state)
            assert await state.get_state() is None
            client.save_result.assert_not_awaited()
            return

        for i, question in enumerate(questionnaire.questions):
            data = AnswerCallback(test_id=1, attempt_id=saved["attempt_id"], question_id=question.id, value=2)
            await answer_question(cq, data, state, client)
            if i == 0:
                await answer_question(cq, data, state, client)
                progress = await state.get_data()
                assert progress["current_index"] == len(progress["answers"]) == 1

        if outcome == "retry":
            assert len((await state.get_data())["answers"]) == 60
            retry = message.edit_text.await_args.kwargs["reply_markup"].inline_keyboard[0][0]
            await submit_result(cq, AttemptCallback.unpack(retry.callback_data), state, client)
            assert client.save_result.await_args_list[0] == client.save_result.await_args_list[1]
        else:
            client.save_result.assert_awaited_once()
        assert client.save_result.await_args.args[0] == cq.from_user.id
        assert client.save_result.await_args.args[2] == saved["attempt_id"]
        submitted = client.save_result.await_args.args[1]
        assert [a.question_id for a in submitted] == [q.id for q in questionnaire.questions]
        assert await state.get_state() is None
        assert not await state.get_data()
        text = message.edit_text.await_args.args[0]
        assert text.count("медицинским диагнозом") == 1
        assert "&lt;BFI&gt;" in text and "&lt;черта&gt;" in text and "&lt;аспект&gt;" in text

    asyncio.run(run())
