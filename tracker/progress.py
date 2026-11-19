from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Sum
from django.shortcuts import render

from . import analytics
from .models import Exercise, ExerciseSet


@login_required
def progress(request):
    """Show strength trends using only the signed-in user's completed sets."""
    exercise_names = list(
        Exercise.objects.filter(workout__owner=request.user)
        .order_by('name').values_list('name', flat=True).distinct()
    )
    selected = request.GET.get('exercise', '')
    if selected not in exercise_names:
        selected = exercise_names[0] if exercise_names else ''

    sessions = []
    chart = analytics.line_chart([])
    personal_record = None
    total_sets = 0
    if selected:
        grouped = (
            ExerciseSet.objects.filter(
                exercise__workout__owner=request.user,
                exercise__name=selected,
                is_completed=True,
            )
            .values('exercise__workout_id', 'exercise__workout__date', 'exercise__workout__name')
            .annotate(
                max_weight=Max('weight_kg'),
                sets=Count('id'),
                reps=Sum('reps'),
            )
            .order_by('exercise__workout__date', 'exercise__workout_id')
        )
        sessions = [
            {
                'date': item['exercise__workout__date'],
                'workout_name': item['exercise__workout__name'],
                'max_weight': item['max_weight'],
                'sets': item['sets'],
                'reps': item['reps'],
            }
            for item in grouped
        ]
        if sessions:
            # Show one strongest point per day, while keeping separate same-day workouts in history.
            daily_best = {}
            for item in sessions:
                daily_best[item['date']] = max(daily_best.get(item['date'], item['max_weight']), item['max_weight'])
            chart = analytics.line_chart(sorted(daily_best.items()), unit='kg')
            personal_record = max(item['max_weight'] for item in sessions)
            total_sets = sum(item['sets'] for item in sessions)

    return render(request, 'tracker/progress.html', {
        'exercise_names': exercise_names,
        'selected': selected,
        'sessions': list(reversed(sessions)),
        'chart': chart,
        'personal_record': personal_record,
        'total_sets': total_sets,
        'session_count': len(sessions),
    })
