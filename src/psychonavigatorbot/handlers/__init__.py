from aiogram import Router

from psychonavigatorbot.handlers.tests import router as router_tests
from psychonavigatorbot.handlers.start import router as router_start


def setup_router() -> Router:
    router = Router()
    router.include_router(router_start)
    router.include_router(router_tests)
    return router
