from django.shortcuts import render

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
    return render(request, 'exercises/exercise_list.html', {'exercises': EXERCISES})