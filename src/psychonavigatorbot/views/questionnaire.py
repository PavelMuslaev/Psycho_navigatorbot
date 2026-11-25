from html import escape
from psychonavigatorbot.models.attempt import QuestionnaireAttempt
from psychonavigatorbot.models.test_results import QuestionnaireResult


def format_question(attempt: QuestionnaireAttempt) -> str:
    question = attempt.questions[attempt.current_index]
    return (
        f"🧠 <b>{escape(attempt.questionnaire_name)}</b>\n\n"
        f"<b>Вопрос {attempt.current_index + 1} из {len(attempt.questions)}</b>\n\n"
        f"{escape(question.text)}"
    )


def format_ready(attempt: QuestionnaireAttempt) -> str:
    return (
        f"<b>{escape(attempt.questionnaire_name)}</b>\n\n"
        f"Вы ответили на все вопросы: {len(attempt.answers)}.\n"
        "Нажмите «Рассчитать результат»."
    )


def format_result(name: str, result: QuestionnaireResult) -> str:
    lines = [f"✅ <b>{escape(name)}</b>", "", "<b>Ваш результат:</b>"]
    for domain in result.domains:
        lines.append(f"\n<b>{escape(domain.name)}</b>: {domain.score:.2f}")
        for facet in domain.facets:
            lines.append(f"• {escape(facet.name)}: {facet.score:.2f}")
            lines.extend(
                [
                    "",
                    "<i>Результат является описательным профилем и не медицинским диагнозом.</i>",
                ]
            )
    return "\n".join(lines)
