"""
The daily drill: spaced repetition over what the learner has already studied.

Questions come from two sources — the hand-authored MCQs in each module, and
model-generated practice questions seeded from the module's theory. The
authored bank is about 96 questions, which one committed user exhausts in a
weekend; generation is what keeps the drill from running dry.

Scheduling is per user and per card, so the same question does not appear two
days running and the pool grows with every module completed.
"""

from __future__ import annotations

import logging
from datetime import date

from ai import tutor
from courses import content
from courses.models import UserCourseProgress

from .models import ReviewCard

logger = logging.getLogger(__name__)

DRILL_SIZE = 5


def sync_cards(user) -> int:
    """Enrol questions from every module the user has completed.

    Returns the number of new cards. Safe to call repeatedly: cards are keyed on
    ``question_id``, so re-running only picks up newly completed modules.
    """
    completed = UserCourseProgress.objects.filter(user=user, status='completed').exclude(module_id='')
    known = set(ReviewCard.objects.filter(user=user).values_list('question_id', flat=True))

    new_cards = []
    for progress in completed:
        module = content.get_module(progress.course_id, progress.module_id)
        if not module:
            continue

        for question in _questions_for(module):
            question_id = f'{module["course_id"]}:{module["id"]}:{question["id"]}'
            if question_id in known:
                continue

            known.add(question_id)
            new_cards.append(
                ReviewCard(
                    user=user,
                    course_id=module['course_id'],
                    module_id=module['id'],
                    question_id=question_id,
                    question=question['question'],
                    options=question['options'],
                    correct_index=question['correct_index'],
                    explanation=question.get('explanation', ''),
                )
            )

    if new_cards:
        ReviewCard.objects.bulk_create(new_cards, ignore_conflicts=True)
    return len(new_cards)


def _questions_for(module: dict) -> list[dict]:
    """Authored questions plus generated ones, in that order."""
    questions = list(module['mcqs'])

    generated = tutor.generate_drill_questions(module['title'], module['theory'], count=3)
    for index, question in enumerate(generated or []):
        questions.append(
            {
                'id': f'gen-{index}',
                'question': question['question'],
                'options': question['options'],
                'correct_index': question['correct_index'],
                'explanation': question.get('explanation', ''),
            }
        )

    return questions


def todays_drill(user, size: int = DRILL_SIZE) -> list[ReviewCard]:
    """Cards due today, hardest first.

    Sorting by lapses puts the material the learner keeps getting wrong at the
    front, while they are still fresh.
    """
    due = ReviewCard.objects.filter(user=user, due_on__lte=date.today()).order_by('-lapses', 'due_on')[:size]

    if len(due) >= size:
        return list(due)

    # Not enough due: top up with the cards closest to becoming due, so the
    # drill is always a full set rather than a short one.
    ids = [card.id for card in due]
    upcoming = (
        ReviewCard.objects.filter(user=user)
        .exclude(id__in=ids)
        .order_by('due_on')[: size - len(ids)]
    )

    return list(due) + list(upcoming)


def serialise(card: ReviewCard) -> dict:
    """Card for the client, with the answer withheld."""
    return {
        'id': card.id,
        'question': card.question,
        'options': card.options,
        'course_id': card.course_id,
        'module_id': card.module_id,
        'seen_before': card.reviews > 0,
    }


def answer(card: ReviewCard, chosen_index: int) -> dict:
    """Grade an answer, reschedule the card, and explain a miss.

    The explanation is generated only when the learner got it wrong and the
    card carries no authored one, so the model is not asked for something the
    content already provides.
    """
    correct = chosen_index == card.correct_index
    card.review(correct)

    explanation = card.explanation
    if not correct and not explanation:
        explanation = (
            tutor.explain_wrong_answer(
                card.question,
                chosen=card.options[chosen_index] if 0 <= chosen_index < len(card.options) else 'nothing',
                correct=card.options[card.correct_index],
                module_title=card.module_id,
            )
            or ''
        )

    return {
        'correct': correct,
        'correct_index': card.correct_index,
        'explanation': explanation,
        'next_review_in_days': card.interval_days,
    }
