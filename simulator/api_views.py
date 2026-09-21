"""
Scenario runs: a short sequence of financial decisions with consequences.

Two things this rewrite changes.

**Scoring moved server-side.** The client used to POST the score it thought its
choice was worth, and the server stored it. Anyone could send ``score: 9999``.
The score now comes from the chosen option in the database and the request only
carries which option was picked.

**A running balance.** Each scenario's starting balance used to be shown as
"current capital", so the number jumped from ₹1,00,000 to ₹30,000 between
questions and looked like a loss. A run now carries one balance that each
decision moves.
"""

from __future__ import annotations

import random

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import UserProfile

from .models import DecisionOption, QuizRun, Scenario, UserScenarioAttempt

SCENARIOS_PER_RUN = 4
XP_PER_POINT = 2

# Used to project a decision forward when the option carries no explicit growth
# rate. Most seeded options leave it at zero, which drew "now" and "in a year"
# as two identical bars. These are illustrative long-run rates, not forecasts.
DEFAULT_GROWTH = {'INVEST': 0.12, 'SAVE': 0.06, 'SPEND': 0.0}


def _serialise_scenario(scenario: Scenario, run: QuizRun, position: int, total: int) -> dict:
    """The current question. Option scores are withheld until it is answered."""
    return {
        'run_id': run.id,
        'question_number': position + 1,
        'total_questions': total,
        'running_balance': float(run.running_balance),
        'total_score': run.total_score,
        'scenario': {
            'id': scenario.id,
            'title': scenario.title,
            'description': scenario.description,
        },
        'choices': [
            {'id': option.id, 'text': option.text, 'type': option.decision_type}
            for option in scenario.options.all()
        ],
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz_api(request):
    """Begin a run of randomly chosen scenarios."""
    ids = list(Scenario.objects.values_list('id', flat=True))
    if not ids:
        return Response({'error': 'No scenarios are loaded.'}, status=503)

    chosen = random.sample(ids, min(SCENARIOS_PER_RUN, len(ids)))

    run = QuizRun.objects.create(
        user=request.user,
        scenario_ids=','.join(map(str, chosen)),
        current_question_index=0,
        total_score=0,
        running_balance=Scenario.objects.get(id=chosen[0]).starting_balance,
    )

    return Response({'success': True, 'run_id': run.id})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_question(request, run_id):
    """The current question, or the completion marker."""
    run = get_object_or_404(QuizRun, id=run_id, user=request.user)
    scenarios = run.get_scenario_list()

    if run.is_completed or run.current_question_index >= len(scenarios):
        if not run.is_completed:
            run.is_completed = True
            run.save(update_fields=['is_completed'])
        return Response({'completed': True, 'run_id': run.id})

    scenario = get_object_or_404(Scenario, id=scenarios[run.current_question_index])
    return Response(_serialise_scenario(scenario, run, run.current_question_index, len(scenarios)))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer_api(request):
    """Record a choice, score it from the database, and advance the run."""
    run = get_object_or_404(QuizRun, id=request.data.get('run_id'), user=request.user)

    if run.is_completed:
        return Response({'error': 'This run is already finished.'}, status=400)

    scenarios = run.get_scenario_list()
    scenario = get_object_or_404(Scenario, id=scenarios[run.current_question_index])

    option = DecisionOption.objects.filter(
        id=request.data.get('option_id'), scenario=scenario
    ).first()
    if option is None:
        return Response({'error': 'That choice is not part of this scenario.'}, status=400)

    options = list(scenario.options.all())
    best_score = max((o.score for o in options), default=0)
    was_best = option.score >= best_score and option.score > 0

    run.total_score += option.score
    run.running_balance += option.balance_impact
    run.current_question_index += 1
    if run.current_question_index >= len(scenarios):
        run.is_completed = True
    run.save()

    UserScenarioAttempt.objects.update_or_create(
        user=request.user,
        scenario=scenario,
        quiz_run=run,
        defaults=dict(
            chosen_option=option,
            score_earned=option.score,
            is_correct=was_best,
        ),
    )

    growth = float(option.future_growth_rate) or DEFAULT_GROWTH.get(option.decision_type, 0.0)
    projected = float(run.running_balance) * (1 + growth)

    return Response(
        {
            'score_earned': option.score,
            'best_available': best_score,
            'was_best_choice': was_best,
            'running_balance': float(run.running_balance),
            'balance_change': float(option.balance_impact),
            'projected_one_year': round(projected, 2),
            'growth_rate_percent': round(growth * 100, 1),
            'why_it_matters': option.why_it_matters,
            'mentor_feedback': option.mentor_feedback,
            'better_choice': (
                None
                if was_best
                else next(
                    (o.text for o in options if o.score == best_score and o.id != option.id),
                    None,
                )
            ),
            'total_score': run.total_score,
            'completed': run.is_completed,
            'next_question': run.current_question_index + 1,
            'total_questions': len(scenarios),
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_result(request, run_id):
    """Final score, XP, and a per-decision breakdown."""
    run = get_object_or_404(QuizRun, id=run_id, user=request.user)
    scenarios = run.get_scenario_list()

    max_score = sum(
        max((o.score for o in Scenario.objects.get(id=sid).options.all()), default=0)
        for sid in scenarios
    )

    xp = 0
    if run.is_completed and not run.xp_awarded:
        xp = run.total_score * XP_PER_POINT
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += xp
        profile.save(update_fields=['xp'])
        run.xp_awarded = True
        run.save(update_fields=['xp_awarded'])

    attempts = (
        UserScenarioAttempt.objects.filter(user=request.user, scenario_id__in=scenarios)
        .select_related('scenario', 'chosen_option')
        .order_by('-id')[: len(scenarios)]
    )

    return Response(
        {
            'run_id': run.id,
            'total_score': run.total_score,
            'max_score': max_score,
            'accuracy': round(run.total_score / max_score * 100) if max_score else 0,
            'final_balance': float(run.running_balance),
            'xp_awarded': xp,
            'decisions': [
                {
                    'scenario': attempt.scenario.title,
                    'choice': attempt.chosen_option.text if attempt.chosen_option else '',
                    'score': attempt.score_earned,
                    'was_best': attempt.is_correct,
                    'why': attempt.chosen_option.why_it_matters if attempt.chosen_option else '',
                }
                for attempt in reversed(list(attempts))
            ],
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scenarios_list(request):
    """Every scenario, for the browse view."""
    return Response(
        {
            'scenarios': [
                {
                    'id': scenario.id,
                    'title': scenario.title,
                    'description': scenario.description,
                    'choices': scenario.options.count(),
                }
                for scenario in Scenario.objects.prefetch_related('options')
            ]
        }
    )
