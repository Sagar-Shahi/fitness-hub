from django.shortcuts import render
from goals.models import Goal

# Create your views here.

EXERCISES = [
    {
        'title': 'Full-Body Strength Session',
        'description': 'Build strength with a balanced mix of compound lifts and functional moves.',
        'duration': '30 mins',
    },
    {
        'title': 'Core & Mobility Flow',
        'description': 'Improve stability and flexibility with core-focused mobility work.',
        'duration': '25 mins',
    },
    {
        'title': 'HIIT Conditioning',
        'description': 'High intensity interval training for cardio, fat burn, and endurance.',
        'duration': '20 mins',
    },
    {
        'title': 'Recovery Stretch Routine',
        'description': 'A gentle sequence to recover faster and reduce muscle soreness.',
        'duration': '15 mins',
    },
]

def index(request):
    return render(request, 'index.html')


def exercise_list(request):
    from .models import Exercise

    def _parse_steps(text):
        if not text:
            return {'setup_steps': [], 'movement_steps': []}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        setup = []
        movement = []
        joined = '\n'.join(lines)
        if 'Setup:' in joined or 'Movement:' in joined:
            curr = None
            for line in lines:
                if line.lower().startswith('setup:'):
                    curr = 'setup'
                    content = line.split(':', 1)[1].strip()
                    if content:
                        setup.append(content)
                    continue
                if line.lower().startswith('movement:'):
                    curr = 'movement'
                    content = line.split(':', 1)[1].strip()
                    if content:
                        movement.append(content)
                    continue
                if curr == 'setup':
                    setup.append(line)
                elif curr == 'movement':
                    movement.append(line)
                else:
                    movement.append(line)
        else:
            if not lines:
                return {'setup_steps': [], 'movement_steps': []}
            split_at = max(1, len(lines) // 3)
            setup = lines[:split_at]
            movement = lines[split_at:]

        return {'setup_steps': setup, 'movement_steps': movement}

    exercises_qs = Exercise.objects.all()
    exercises = []
    active_goal = None
    selected_goal = None
    focus_areas = []
    if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        active_goal = Goal.objects.filter(user=request.user).order_by('-id').first()
        if active_goal:
            selected_goal = active_goal.goal_type
            focus_areas = active_goal.focus_areas or []
            if not active_goal.assigned_exercises.exists():
                active_goal.sync_assigned_exercises()
        else:
            prof = getattr(request.user, 'profile', None)
            selected_goal = getattr(prof, 'selected_goal', None)

    if request.GET.get('selectedGoal'):
        selected_goal = request.GET.get('selectedGoal')

    from .goal_logic import filter_exercises_by_goal, adjust_reps_sets_for_body_type

    if exercises_qs.exists():
        ex_list = []
        for ex in exercises_qs:
            ex_list.append({
                'name': ex.name,
                'slug': ex.slug,
                'description': ex.description,
                'duration': getattr(ex, 'duration', ''),
                'image_url': ex.image_url,
                'video_url': ex.video_url,
                'category': ex.category,
                'equipment': ex.equipment,
                'steps': ex.steps,
                'form_tips': ex.form_tips or ex.safety or '',
                'default_reps': 8,
                'default_sets': 3,
            })

            recommended = set()
        show_all = selected_goal == 'my_plan'
        if selected_goal and not show_all:
            filtered = filter_exercises_by_goal(ex_list, selected_goal, focus_areas)
            recommended = {item.get('slug') for item in filtered}
        else:
            filtered = []

        body_type = None
        if hasattr(request.user, 'profile'):
            body_type = getattr(request.user.profile, 'body_type', None)

        for ex in ex_list:
            steps_text = ex.get('steps') if isinstance(ex, dict) else getattr(ex, 'steps', '')
            parsed = _parse_steps(steps_text)
            base_reps = ex.get('default_reps', 8)
            base_sets = ex.get('default_sets', 3)
            reps_sets = adjust_reps_sets_for_body_type(base_reps, base_sets, body_type)
            exercises.append({
                'name': ex.get('name'),
                'slug': ex.get('slug'),
                'description': ex.get('description'),
                'duration': ex.get('duration'),
                'image_url': ex.get('image_url'),
                'video_url': ex.get('video_url'),
                'setup_steps': parsed['setup_steps'],
                'movement_steps': parsed['movement_steps'],
                'form_tips': ex.get('form_tips', ''),
                'reps': reps_sets['reps'],
                'sets': reps_sets['sets'],
                'recommended': ex.get('slug') in recommended,
            })
    else:
        fallback_recommended = set()
        if selected_goal and selected_goal != 'my_plan':
            fallback_filtered = filter_exercises_by_goal(EXERCISES, selected_goal, focus_areas)
            fallback_recommended = {item.get('slug') for item in fallback_filtered}

        for e in EXERCISES:
            slug = e.get('title', '').lower().replace(' ', '-')
            exercises.append({
                'name': e.get('title'),
                'slug': slug,
                'description': e.get('description'),
                'duration': e.get('duration'),
                'goal': e.get('goal', 'General'),
                'image_url': e.get('image_url', ''),
                'video_url': e.get('video_url', ''),
                'setup_steps': [],
                'movement_steps': [],
                'form_tips': '',
                'recommended': slug in fallback_recommended,
            })

    exercises.sort(key=lambda item: (not item.get('recommended', False), item['name']))

    return render(request, 'exercises/exercise_list.html', {
        'exercises': exercises,
        'active_goal': active_goal,
        'selected_goal': selected_goal,
        'focus_areas': focus_areas,
    })


def exercise_detail(request, slug):
    from .models import Exercise
    ex = Exercise.objects.filter(slug=slug).first()
    if not ex:
        return render(request, '404.html', status=404)
    return render(request, 'exercises/exercise_detail.html', {'exercise': ex})