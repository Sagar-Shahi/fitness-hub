"""Knowledge base for the Fitness Hub chatbot.

Pulls exercise data live from the DB and combines it with a curated FAQ about
the app's features. Everything the bot can answer is sourced from here, so
it can never invent information that isn't backed by real data.
"""


APP_FEATURES = {
    'workouts': {
        'title': 'Workout Library',
        'path': '/exercises/',
        'summary': "Browse 36 exercises across 7 muscle groups, ranked against your active goal.",
        'keywords': ['workout', 'workouts', 'library', 'exercise', 'exercises', 'training', 'routine'],
    },
    'records': {
        'title': 'Workout Records',
        'path': '/users/records/',
        'summary': "Every exercise you mark complete is auto-logged here, grouped by day.",
        'keywords': ['record', 'records', 'log', 'logs', 'history'],
    },
    'progress': {
        'title': 'Workout Log',
        'path': '/progress/',
        'summary': "See your logged workouts, weekly volume, and goal alignment.",
        'keywords': ['progress', 'volume', 'streak', 'alignment'],
    },
    'goals': {
        'title': 'Your Goals',
        'path': '/goals/',
        'summary': "Create, track, and crush fitness goals. Drives exercise recommendations.",
        'keywords': ['goal', 'goals', 'objective', 'target'],
    },
    'diet': {
        'title': 'Diet Planner',
        'path': '/diet/',
        'summary': "Clinical BMR / TDEE targets, macros, food tracker, and budget meals.",
        'keywords': ['diet', 'nutrition', 'calorie', 'calories', 'macro', 'macros', 'meal', 'meals', 'food', 'tdee', 'bmr'],
    },
    'store': {
        'title': 'Store',
        'path': '/store/',
        'summary': "Outfits, gear, and supplements. Cart, checkout, and order history included.",
        'keywords': ['store', 'shop', 'shopping', 'product', 'products', 'gear', 'supplement', 'supplements'],
    },
    'cart': {
        'title': 'Cart',
        'path': '/store/cart/',
        'summary': "Review your items, adjust quantities, and proceed to checkout.",
        'keywords': ['cart', 'basket'],
    },
    'orders': {
        'title': 'My Orders',
        'path': '/store/orders/',
        'summary': "Track and review every order you've placed.",
        'keywords': ['order', 'orders', 'purchase', 'purchases', 'tracking'],
    },
    'checkout': {
        'title': 'Checkout',
        'path': '/store/checkout/',
        'summary': "Three-step checkout: contact info, shipping, payment.",
        'keywords': ['checkout', 'payment', 'pay'],
    },
    'inspiration': {
        'title': 'Inspiration',
        'path': '/inspiration/',
        'summary': "Daily quote, 13 athlete profiles, training principles, and videos.",
        'keywords': ['inspiration', 'motivation', 'quote', 'quotes', 'icon', 'icons', 'athlete'],
    },
    'profile': {
        'title': 'Profile',
        'path': '/users/profile/',
        'summary': "Your account info, body stats, and goal at a glance.",
        'keywords': ['profile', 'account info', 'my profile'],
    },
    'settings': {
        'title': 'Settings',
        'path': '/users/settings/',
        'summary': "Change your username, password, email, and other account details.",
        'keywords': ['settings', 'change password', 'change username', 'change email', 'password', 'username', 'security'],
    },
    'dashboard': {
        'title': 'Dashboard',
        'path': '/dashboard/',
        'summary': "Your training overview: streaks, weekly volume, active goal, next workout.",
        'keywords': ['dashboard', 'overview'],
    },
}

GOAL_DESCRIPTIONS = {
    'general':       'A balanced mix of strength, mobility, and cardio.',
    'strength':      'Heavier compound lifts at low reps to build maximal strength.',
    'hypertrophy':   'Moderate weight, higher volume, short rest — built for muscle growth.',
    'endurance':     'Lighter weight and longer sets to build muscular endurance.',
    'mobility':      'Slow, controlled movement through full range of motion.',
    'flexibility':   'Stretching-focused work to lengthen muscles and improve range.',
    'weight_loss':   'Higher-volume circuits with shorter rest to burn calories.',
}

CATEGORY_DESCRIPTIONS = {
    'chest':    'Pushing movements that work the pecs, front delts, and triceps.',
    'back':     'Pulling movements for the lats, traps, rhomboids, and biceps.',
    'shoulders': 'Overhead and lateral work for the deltoids and upper traps.',
    'arms':     'Biceps, triceps, and forearms.',
    'legs':     'Quads, hamstrings, glutes, and calves.',
    'core':     'Abs, obliques, and lower back for stability.',
    'cardio':   'Conditioning work that raises the heart rate.',
}

DIFFICULTY_DESCRIPTIONS = {
    'beginner':     'Good if you’re new to training or returning after a break. Focus on form over load.',
    'intermediate': 'For people with 3–6 months of consistent training.',
    'advanced':     'Assumes solid technique and a strong base. Higher intensity and complexity.',
}

NUTRITION_FAQ = [
    {
        'q': ['how many calories', 'calorie target', 'how much should i eat'],
        'a': (
            "Your daily calorie target is calculated from your BMR (basal metabolic rate) "
            "and TDEE (total daily energy expenditure) using the Harris–Benedict formula, "
            "adjusted for your activity level and goal. Open the Diet Planner and the numbers "
            "are right at the top."
        ),
    },
    {
        'q': ['how much protein', 'protein intake', 'protein per day'],
        'a': (
            "A common evidence-based range is 1.6–2.2 g of protein per kg of bodyweight per day "
            "for active people. If you’re in a cut, lean toward the higher end to preserve muscle. "
            "Use the Diet Planner to see your personal gram target."
        ),
    },
    {
        'q': ['what should i eat before', 'pre workout meal', 'pre-workout food'],
        'a': (
            "1–2 hours before training, a meal with carbs + moderate protein works well "
            "(oats + Greek yoghurt, rice + chicken, a banana + peanut butter). Keep fat and "
            "fibre moderate so it doesn’t sit heavy."
        ),
    },
    {
        'q': ['what should i eat after', 'post workout meal', 'post-workout food'],
        'a': (
            "Within ~2 hours after training, eat a meal with protein (≈0.3 g/kg) and carbs "
            "to refuel. A protein shake + rice + vegetables, or eggs + toast + fruit, both work."
        ),
    },
    {
        'q': ['cheap meals', 'budget meals', 'low cost meals'],
        'a': (
            "Open Diet Planner → Budget Meals. We pre-plan affordable meals with full macro "
            "breakdowns (eggs, oats, beans, rice, frozen veg, chicken thigh, canned fish)."
        ),
    },
    {
        'q': ['is creatine safe', 'creatine supplement'],
        'a': (
            "Creatine monohydrate is one of the most studied supplements in sports science. "
            "3–5 g per day is the standard dose. It is safe for healthy adults. Drink enough water."
        ),
    },
    {
        'q': ['protein powder', 'whey protein', 'should i use protein powder'],
        'a': (
            "Protein powder is just food. Use it to hit your daily protein target if it’s hard "
            "to get from whole foods. Whey, casein, or plant proteins are all fine — pick one "
            "you tolerate and like the taste of."
        ),
    },
]

GENERAL_FITNESS_FAQ = [
    {
        'q': ['how often should i train', 'how many days a week', 'training frequency'],
        'a': (
            "Most people do well with 3–5 training days per week. Beginners often start at 3 "
            "full-body days; intermediate/advanced lifters usually split into upper/lower or "
            "push/pull/legs. Sleep and recovery matter as much as the sessions."
        ),
    },
    {
        'q': ['how long should a workout be', 'workout duration', 'how long to train'],
        'a': (
            "45–75 minutes is a sweet spot. Longer than ~90 minutes usually means you’re either "
            "resting too much, doing too much volume, or training inefficiently."
        ),
    },
    {
        'q': ['should i do cardio', 'do i need cardio', 'cardio vs weights'],
        'a': (
            "Both have value. Strength training builds muscle, protects joints, and raises your "
            "resting metabolism. Cardio is great for heart health, work capacity, and calorie "
            "burn. The best plan is whatever you’ll do consistently. Most people do well with "
            "2–3 cardio sessions a week plus their strength work."
        ),
    },
    {
        'q': ['how do i lose weight', 'lose fat', 'fat loss'],
        'a': (
            "Fat loss is mostly about being in a moderate calorie deficit (≈300–500 kcal/day) "
            "over weeks, eating enough protein, and training hard enough to keep your muscle. "
            "Use the Diet Planner to compute your target, log your food honestly, and lift weights."
        ),
    },
    {
        'q': ['how do i build muscle', 'gain muscle', 'hypertrophy how'],
        'a': (
            "Three things, in order of importance: (1) eat in a small calorie surplus or at "
            "maintenance with enough protein (1.6–2.2 g/kg), (2) train each muscle 2x per week "
            "with progressive overload, (3) sleep 7–9 hours. Use the Hypertrophy filter in the "
            "Workout Library to start."
        ),
    },
    {
        'q': ['i pulled a muscle', 'i am sore', 'soreness', 'doms'],
        'a': (
            "Mild soreness 24–72 hours after training is normal (DOMS). Light movement, walking, "
            "and sleep help. If you feel sharp or sudden pain during a lift, stop. If pain "
            "persists for more than a few days, see a physiotherapist or doctor."
        ),
    },
    {
        'q': ['how much water', 'water intake', 'how much water should i drink'],
        'a': (
            "A practical starting point is 30–40 ml per kg of bodyweight per day, more on hot "
            "days or heavy training days. Pale yellow urine is a good visual signal."
        ),
    },
    {
        'q': ['warm up', 'how to warm up', 'do i need to warm up'],
        'a': (
            "Yes. 5 minutes of light cardio to raise body temperature, then 1–2 warm-up sets "
            "of the exercise you’re about to do, ramping up in weight, before your working sets."
        ),
    },
]


def get_exercise_by_name(name: str):
    from exercises.models import Exercise
    qs = Exercise.objects.all()
    name_l = name.lower()
    for ex in qs:
        if ex.name.lower() == name_l:
            return ex
    for ex in qs:
        if name_l in ex.name.lower() or ex.name.lower() in name_l:
            return ex
    return None


def search_exercises(query: str, limit: int = 5):
    from exercises.models import Exercise
    import re
    q = (query or '').lower().strip()
    if not q:
        return []
    # Strip punctuation from each token so "push-up?" matches "push-up".
    words = []
    for w in q.split():
        clean = re.sub(r'[^a-z0-9\'-]', '', w)
        if len(clean) >= 3:
            words.append(clean)
    qs = Exercise.objects.all()
    scored = []
    for ex in qs:
        hay = ' '.join([
            ex.name.lower(), ex.category.lower(),
            (ex.target_muscles or '').lower(), (ex.equipment or '').lower(),
            ex.goal.lower(), (ex.description or '').lower(),
        ])
        score = sum(1 for w in words if w in hay)
        if score > 0:
            scored.append((score, ex))
    scored.sort(key=lambda t: (-t[0], t[1].name))
    return [ex for _, ex in scored[:limit]]


def list_exercises_by_category(category: str):
    from exercises.models import Exercise
    return Exercise.objects.filter(category=category).order_by('name')


def list_exercises_by_goal(goal: str):
    from exercises.models import Exercise
    return Exercise.objects.filter(goal=goal).order_by('name')


def list_exercises_by_difficulty(difficulty: str):
    from exercises.models import Exercise
    return Exercise.objects.filter(difficulty=difficulty).order_by('name')


def get_app_feature(name: str):
    name_l = (name or '').lower()
    for key, feat in APP_FEATURES.items():
        if name_l in key or name_l in feat['title'].lower():
            return key, feat
    for key, feat in APP_FEATURES.items():
        if any(k in name_l for k in feat['keywords']):
            return key, feat
    return None, None


def find_app_route_for_query(text: str):
    """Return (key, feature) if the user seems to be asking how to do something in the app."""
    t = (text or '').lower()
    for key, feat in APP_FEATURES.items():
        if any(k in t for k in feat['keywords']):
            return key, feat
    return None, None


def find_faq_answer(text: str):
    t = (text or '').lower()
    for entry in NUTRITION_FAQ + GENERAL_FITNESS_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None
