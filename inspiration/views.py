from django.shortcuts import render

INSPIRATION_FEED = [
    {
        'title': 'Consistency Beats Perfection',
        'author': 'Coach Sarah',
        'excerpt': 'Small actions done consistently create big results. Start today, no matter how small.',
        'date': '2026-06-01',
    },
    {
        'title': '5 Post-Workout Recovery Tips',
        'author': 'Dr. James',
        'excerpt': 'Learn how to maximize recovery with nutrition, sleep, and mobility work.',
        'date': '2026-05-29',
    },
    {
        'title': 'Mental Strength Through Training',
        'author': 'Alex M.',
        'excerpt': 'How fitness teaches us discipline and resilience for life beyond the gym.',
        'date': '2026-05-27',
    },
]

def inspiration_feed(request):
    return render(request, 'inspiration/inspiration_feed.html', {'posts': INSPIRATION_FEED})
