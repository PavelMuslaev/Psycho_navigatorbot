from aiogram.fsm.state import State, StatesGroup


class QuestionnaireState(StatesGroup):
    answering = State()
    ready_to_submit = State()
    submitting = State()
