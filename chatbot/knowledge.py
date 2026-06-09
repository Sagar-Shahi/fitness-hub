"""Knowledge base for the Fitness Hub chatbot.

Pulls exercise data live from the DB and combines it with a curated FAQ about
the app's features. Everything the bot can answer is sourced from here, so
it can never invent information that isn't backed by real data.
"""


# ---------------------------------------------------------------------------
# App features — every page, every action the bot can point the user to.
# ---------------------------------------------------------------------------

APP_FEATURES = {
    'workouts': {
        'title': 'Workout Library',
        'path': '/exercises/',
        'summary': "Browse 36 exercises across 7 muscle groups, ranked against your active goal.",
        'how': (
            "**Workout Library** lives at `/exercises/`. Open it to see every exercise in the app, "
            "filtered by muscle group and your active goal. Click any exercise to read its "
            "description, form tips, common mistakes, and breathing cues. From there you can "
            "hit **Mark Complete & Log** for a one-tap log, or **Log With Details** to record "
            "reps, hold time, and notes."
        ),
        'keywords': ['workout', 'workouts', 'workout library', 'library', 'exercise', 'exercises', 'training', 'routine', 'exercising', 'work out'],
    },
    'records': {
        'title': 'Workout Records',
        'path': '/users/records/',
        'summary': "Every exercise you mark complete is auto-logged here, grouped by day.",
        'how': (
            "**Records** (`/users/records/`) shows every session you've ever logged, grouped by "
            "date. Each day card lists the exercises, total reps, total minutes, and total "
            "calories. The page auto-updates the moment you tap **Mark Complete** in the "
            "Workout Library — you never have to enter anything manually."
        ),
        'keywords': ['record', 'records', 'log', 'logs', 'history', 'workout history', 'exercise records', 'past sessions'],
    },
    'progress': {
        'title': 'Workout Log / Progress',
        'path': '/progress/',
        'summary': "See your logged workouts, weekly volume, and goal alignment.",
        'how': (
            "**Progress** (`/progress/`) is your training overview: total sessions, weekly "
            "volume (sets × reps), current streak, and how well your recent sessions align "
            "with the goal you've set. The page updates after every logged session."
        ),
        'keywords': ['progress', 'volume', 'streak', 'alignment'],
    },
    'goals': {
        'title': 'Your Goals',
        'path': '/goals/',
        'summary': "Create, track, and crush fitness goals. Drives exercise recommendations.",
        'how': (
            "**Goals** (`/goals/`) is where you set your primary fitness goal — strength, "
            "hypertrophy, endurance, mobility, flexibility, or weight loss. The whole app "
            "tunes to this: workout recommendations, diet macros, and progress alignment "
            "all use it. Change it any time and the system re-prioritizes immediately."
        ),
        'keywords': ['goal', 'goals', 'objective', 'target', 'focus', 'aim', 'purpose', 'milestone'],
    },
    'diet': {
        'title': 'Diet Planner',
        'path': '/diet/',
        'summary': "Clinical BMR / TDEE targets, macros, food tracker, and budget meals.",
        'how': (
            "**Diet Planner** (`/diet/`) uses the Harris–Benedict equation to compute your "
            "BMR and TDEE from your height, weight, age, gender, and activity level. From "
            "there it derives daily calorie and macro targets for your active goal. Sub-pages:\n"
            "• **Suggest** (`/diet/suggest/`) — your full plan with food suggestions\n"
            "• **Foods** (`/diet/foods/`) — click foods to build a meal, totals update live\n"
            "• **Budget Meals** (`/diet/budget-meals/`) — pre-planned affordable meals\n"
            "• **Add Record** (`/diet/create/`) — log what you actually ate"
        ),
        'keywords': ['diet', 'nutrition', 'calorie', 'calories', 'macro', 'macros', 'meal', 'meals', 'food', 'tdee', 'bmr'],
    },
    'store': {
        'title': 'Store',
        'path': '/store/',
        'summary': "Outfits, gear, and supplements. Cart, checkout, and order history included.",
        'how': (
            "**Store** (`/store/`) is the in-app shop: apparel, equipment, and supplements. "
            "Browse by category on the home page, search by name, or open **All products** "
            "(`/store/products/`). Each product page shows price, rating, stock, and an "
            "**Add to Cart** button. Free shipping kicks in at NRS 5000."
        ),
        'keywords': ['store', 'shop', 'shopping', 'product', 'products', 'gear', 'supplement', 'supplements', 'catalog', 'category', 'merchandise', 'items', 'buy'],
    },
    'cart': {
        'title': 'Cart',
        'path': '/store/cart/',
        'summary': "Review your items, adjust quantities, and proceed to checkout.",
        'how': (
            "**Cart** (`/store/cart/`) lists everything you've added. Use the − / + buttons "
            "to change quantities (it auto-saves), or hit **Remove**. The right-hand summary "
            "shows subtotal, shipping, tax, and total in NRS. When you're ready, click "
            "**Proceed to Checkout**."
        ),
        'keywords': ['cart', 'basket'],
    },
    'orders': {
        'title': 'My Orders',
        'path': '/store/orders/',
        'summary': "Track and review every order you've placed.",
        'how': (
            "**My Orders** (`/store/orders/`) is your purchase history. Each card shows the "
            "order number, date, status, item thumbnails, and total. Click any order to see "
            "the full breakdown: items, shipping address, payment method, payment status, and "
            "a tracker-style progress bar."
        ),
        'keywords': ['order', 'orders', 'purchase', 'purchases', 'tracking'],
    },
    'checkout': {
        'title': 'Checkout',
        'path': '/store/checkout/',
        'summary': "Three-step checkout: contact info, shipping, payment.",
        'how': (
            "**Checkout** (`/store/checkout/`) is a single page with contact info, shipping "
            "address, and payment method (Credit/Debit Card or Cash on Delivery). Review the "
            "right-hand summary, then click **Place Order**. You'll land on the order detail "
            "page with your new order number."
        ),
        'keywords': ['checkout', 'payment', 'pay'],
    },
    'inspiration': {
        'title': 'Inspiration',
        'path': '/inspiration/',
        'summary': "Daily quote, 13 athlete profiles, training principles, and videos.",
        'how': (
            "**Inspiration** (`/inspiration/`) is the 'why' side of the app. Open it for a "
            "daily motivational quote, browse 13 athlete profiles, read 10 training "
            "principles, or watch curated training videos. Great for days when you need a "
            "spark before logging a session."
        ),
        'keywords': ['inspiration', 'motivation', 'quote', 'quotes', 'icon', 'icons', 'athlete'],
    },
    'profile': {
        'title': 'Profile',
        'path': '/users/profile/',
        'summary': "Your account info, body stats, and goal at a glance.",
        'how': (
            "**Profile** (`/users/profile/`) is a read-only summary of your account: "
            "username, email, age, height (ft), weight (kg), active goal, body type, and "
            "focus area. To change any of those, open **Settings** (`/users/settings/`)."
        ),
        'keywords': ['profile', 'account info', 'my profile'],
    },
    'settings': {
        'title': 'Settings',
        'path': '/users/settings/',
        'summary': "Change your username, password, email, and other account details.",
        'how': (
            "**Settings hub** (`/users/settings/`) has three sub-pages:\n"
            "• **Account details** (`/users/settings/account/`) — username, first/last name, email\n"
            "• **Password & security** (`/users/settings/password/`) — change your password\n"
            "• **Fitness profile** — age, height (ft), weight (kg), body type, goal focus\n\n"
            "From there you can also reach **Edit profile** (`/users/profile/edit/`) to "
            "update your body stats in detail."
        ),
        'keywords': ['settings', 'change password', 'change username', 'change email', 'password', 'username', 'security', 'preferences'],
    },
    'dashboard': {
        'title': 'Dashboard',
        'path': '/dashboard/',
        'summary': "Your training overview: streaks, weekly volume, active goal, next workout.",
        'how': (
            "**Dashboard** (`/dashboard/`) is the landing page after login: total sessions, "
            "current streak, weekly volume, your active goal, and the next suggested workout. "
            "It's the fastest way to decide what to do next."
        ),
        'keywords': ['dashboard', 'overview', 'home', 'landing'],
    },
    'chatbot': {
        'title': 'Fitness Hub Bot',
        'path': '/chatbot/',
        'summary': "I'm the Fitness Hub bot. I know every page, every feature, and every exercise.",
        'how': (
            "You're already talking to me! I'm the Fitness Hub bot. I can help with "
            "exercise technique, app navigation, and general fitness & nutrition. I never "
            "modify your account data — I'm read-only. To log a workout, head to "
            "`/exercises/`. To set a goal, open `/goals/`."
        ),
        'keywords': ['bot', 'chatbot', 'assistant'],
    },
    'home': {
        'title': 'Home page',
        'path': '/',
        'summary': "The public landing page — hero intro, quick stats, and links to key features.",
        'how': (
            "**Home** (`/`) is the public landing page. You'll find a hero banner, feature "
            "highlights, and quick links to the Workout Library, Diet Planner, Store, and "
            "Inspiration. Log in or register from the top-right nav."
        ),
        'keywords': ['home', 'homepage', 'landing', 'index', 'main page'],
    },
    'about': {
        'title': 'About',
        'path': '/users/about/',
        'summary': "Learn about Fitness Hub — what it is, who it's for, and the team behind it.",
        'how': (
            "**About** (`/users/about/`) tells you what Fitness Hub is — a clinical-grade "
            "fitness tracker with exercise library, diet planner, store, and chatbot. "
            "Open it from the nav or visit `/users/about/` directly."
        ),
        'keywords': ['about', 'about us', 'team', 'who made', 'information'],
    },
    'register': {
        'title': 'Register / Sign Up',
        'path': '/users/register/',
        'summary': "Create an account — free, no credit card needed.",
        'how': (
            "**Register** (`/users/register/`) takes just a few fields: username, email, "
            "password, age, height (ft), weight (kg), and goal. After registering you'll "
            "be logged in automatically and land on the Dashboard."
        ),
        'keywords': ['register', 'sign up', 'signup', 'create account', 'join', 'join now'],
    },
    'login': {
        'title': 'Login / Sign In',
        'path': '/users/login/',
        'summary': "Sign in with your username or email (case-insensitive).",
        'how': (
            "**Login** (`/users/login/`) accepts your username in any case — uppercase, "
            "lowercase, mixed — we handle it. Enter your password, click **Log in**, and "
            "you'll land on your Dashboard. If you're stuck, check the trouble-shooting "
            "tips on the login page."
        ),
        'keywords': ['login', 'log in', 'sign in', 'signin', 'authenticate', 'auth'],
    },
    'exercise_detail': {
        'title': 'Exercise Detail',
        'path': '/exercises/<slug>/',
        'summary': "Full exercise page: description, form tips, common mistakes, breathing, and log options.",
        'how': (
            "**Exercise Detail** (`/exercises/<slug>/`) shows you everything about a single "
            "exercise: full description, target muscles, equipment needed, working sets/reps, "
            "form tips, common mistakes, breathing cues, safety notes, and a video link when "
            "available. From here you can **Mark Complete & Log** or **Log With Details**."
        ),
        'keywords': ['exercise detail', 'exercise page', 'form tips', 'how to do', 'exercise info'],
    },
    'diet_suggest': {
        'title': 'Diet Suggest',
        'path': '/diet/suggest/',
        'summary': "Your personalised meal plan with calorie and macro targets based on your body stats and goal.",
        'how': (
            "**Diet Suggest** (`/diet/suggest/`) computes your BMR and TDEE from your height, "
            "weight, age, gender, and activity level, then derives daily calorie and macro "
            "targets aligned with your active goal. It also suggests breakfast, lunch, dinner, "
            "and snack options with full macro breakdowns."
        ),
        'keywords': ['diet suggest', 'meal plan', 'meal suggestion', 'eating plan', 'what to eat'],
    },
    'diet_foods': {
        'title': 'Diet Foods',
        'path': '/diet/foods/',
        'summary': "Browse common foods with macro profiles — tap any to build a meal.",
        'how': (
            "**Diet Foods** (`/diet/foods/`) lists common foods with calorie, protein, carb, "
            "and fat data. Click a food's serving size to add it to a running meal card on the "
            "right — totals update live. Great for building a meal on the fly."
        ),
        'keywords': ['diet foods', 'food list', 'foods', 'nutrition data', 'food database'],
    },
    'diet_budget_meals': {
        'title': 'Budget Meals',
        'path': '/diet/budget-meals/',
        'summary': "Pre-planned affordable meals with full macro breakdowns — oats, eggs, beans, rice, and more.",
        'how': (
            "**Budget Meals** (`/diet/budget-meals/`) is a collection of affordable, "
            "nutritious pre-planned meals. Each card shows the meal name, a description, "
            "estimated cost, and full macro breakdown (calories, protein, carbs, fat). "
            "Perfect for eating well on a budget."
        ),
        'keywords': ['budget meals', 'cheap meals', 'affordable meals', 'budget food', 'cheap food'],
    },
    'diet_add_record': {
        'title': 'Add Nutrition Record',
        'path': '/diet/create/',
        'summary': "Log what you actually ate — meal type, food items, and macros.",
        'how': (
            "**Add Record** (`/diet/create/`) lets you log a meal: pick meal type (breakfast, "
            "lunch, dinner, snack), add food items with portions, and see calculated macros. "
            "Your records appear on the main Diet page. You can edit or delete them later."
        ),
        'keywords': ['add meal', 'log food', 'add record', 'create record', 'nutrition record', 'meal record', 'log meal'],
    },
    'store_products': {
        'title': 'All Products',
        'path': '/store/products/',
        'summary': "Full product catalog with search, sort, and filter by category.",
        'how': (
            "**All Products** (`/store/products/`) shows every item in the store. Use the "
            "search bar to find by name, sort by price/rating/name, or filter by category. "
            "Click any product to see full details and add it to your cart."
        ),
        'keywords': ['all products', 'product list', 'browse products', 'search products', 'store products'],
    },
    'store_product_detail': {
        'title': 'Product Detail',
        'path': '/store/product/<slug>/',
        'summary': "Full product page: description, price, rating, stock, and Add to Cart button.",
        'how': (
            "**Product Detail** (`/store/product/<slug>/`) shows the product image, "
            "description, price in NRS, rating, stock status, category, and an **Add to Cart** "
            "button. From here you can also jump to your cart or check your orders."
        ),
        'keywords': ['product detail', 'product page', 'item page', 'product info', 'item detail'],
    },
    'order_detail': {
        'title': 'Order Detail',
        'path': '/store/orders/<str:order_number>/',
        'summary': "Full order breakdown: items, shipping address, payment info, and status tracker.",
        'how': (
            "**Order Detail** (`/store/orders/<str:order_number>/`) gives you the complete "
            "picture of a single order: line items with thumbnails, shipping address, payment "
            "method, payment status, and a progress bar tracking order status from Confirmed "
            "to Delivered."
        ),
        'keywords': ['order detail', 'order info', 'track order', 'order status'],
    },
    'inspiration_icons': {
        'title': 'Athlete Icons',
        'path': '/inspiration/icons/',
        'summary': "Browse 13 athlete profiles with their stats, achievements, and training philosophy.",
        'how': (
            "**Athlete Icons** (`/inspiration/icons/`) profiles 13 icons from sports and "
            "fitness. Each card shows their name, sport, nationality, and a brief bio. Click "
            "any profile to read their full story, quote, achievements, and training tips."
        ),
        'keywords': ['athlete icons', 'athlete profile', 'sport icons', 'icon detail', 'athlete bio', 'sports legend'],
    },
    'inspiration_quotes': {
        'title': 'Inspiration Quotes',
        'path': '/inspiration/quotes/',
        'summary': "A wall of motivational quotes to keep you going.",
        'how': (
            "**Quotes** (`/inspiration/quotes/`) is a scrollable wall of motivational fitness "
            "quotes. Great for days when you need a mental boost before training. The home "
            "inspiration page also shows a daily random quote."
        ),
        'keywords': ['inspiration quotes', 'motivational quotes', 'quotes', 'famous quotes'],
    },
    'play_hub': {
        'title': 'Player Hub',
        'path': '/play/',
        'summary': "Your gamification dashboard: level, XP, coins, streak shields, daily quests, and recent badges.",
        'how': (
            "**Player Hub** (`/play/`) is the center of the play system. See your current "
            "level, XP bar, coins, streak shields, today's daily quests, and recently unlocked "
            "badges. From here you can navigate to Badges, Quests, and the Leaderboard. "
            "Level-up announcements and badge unlock toasts appear here automatically."
        ),
        'keywords': ['play hub', 'player hub', 'player page', 'my play', 'play dashboard', 'my level', 'my xp'],
    },
    'play_badges': {
        'title': 'Badges',
        'path': '/play/badges/',
        'summary': "All 17 badges organised by tier: Bronze, Silver, Gold, and Diamond.",
        'how': (
            "**Badges** (`/play/badges/`) shows every badge in the app organised by tier. "
            "Unlocked badges glow with their tier colour; locked ones are dimmed with a "
            "hint about how to earn them. Tiers: Bronze, Silver, Gold, Diamond."
        ),
        'keywords': ['badges', 'badge list', 'all badges', 'achievements', 'medals'],
    },
    'play_quests': {
        'title': 'Quest Board',
        'path': '/play/quests/',
        'summary': "Daily and weekly quests with progress tracking, claim rewards, and re-roll.",
        'how': (
            "**Quest Board** (`/play/quests/`) shows your active daily and weekly quests. "
            "Each card tracks your progress (e.g. \"3/5 workouts\"). Hit **Claim** when "
            "complete to earn XP and coins. Use the **Re-roll** button to swap a quest you "
            "don't like for a fresh one. New quests spawn automatically each day/week."
        ),
        'keywords': ['quests', 'quest board', 'daily quests', 'weekly quests', 'missions', 'challenges'],
    },
    'play_leaderboard': {
        'title': 'Leaderboard',
        'path': '/play/leaderboard/',
        'summary': "Ranked by XP totals — climb the ladder to Transcendent.",
        'how': (
            "**Leaderboard** (`/play/leaderboard/`) ranks all members by total XP. Your row "
            "lights up so you can find yourself fast. There's also a streak leaderboard for "
            "the most consistent trainers. Titles progress: Rookie → Beast → Monster → "
            "Immortal → Transcendent."
        ),
        'keywords': ['leaderboard', 'ranking', 'rank', 'top players', 'scoreboard', 'ladder'],
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


# Map of question keywords -> detailed how-to answer.
APP_HOWTO = [
    {
        'match': ['log a workout', 'mark complete', 'log workout', 'track a workout',
                  'how do i log', 'how to log'],
        'a': (
            "Logging a workout is one tap:\n"
            "1. Open `/exercises/` and pick any exercise.\n"
            "2. Hit **Mark Complete & Log** for a quick log, or **Log With Details** to record "
            "reps, hold time, and notes.\n"
            "That's it — your entry shows up instantly in `/users/records/` and updates your "
            "streak in `/progress/`."
        ),
    },
    {
        'match': ['change my goal', 'set a goal', 'pick a goal', 'new goal', 'update my goal'],
        'a': (
            "Your goal is set in `/goals/`. Open that page, pick a primary fitness goal "
            "(strength, hypertrophy, endurance, mobility, flexibility, or weight loss), choose "
            "a focus area, and save. The whole app re-tunes to it — workout recommendations, "
            "diet macros, and progress alignment all change immediately."
        ),
    },
    {
        'match': ['change my password', 'reset my password', 'update password'],
        'a': (
            "Open **Settings** (`/users/settings/`) → **Password & security** → "
            "**Change password**. Enter your current password, then your new password twice, "
            "and save. You'll stay signed in."
        ),
    },
    {
        'match': ['change my username', 'update username', 'rename'],
        'a': (
            "Open **Settings** (`/users/settings/`) → **Account details** → "
            "**Account settings**. Update the Username field and save. The new name must be "
            "unique across the app."
        ),
    },
    {
        'match': ['change my email', 'update email', 'change email'],
        'a': (
            "Open **Settings** (`/users/settings/`) → **Account details** → "
            "**Account settings**. Update the Email field and save. We use it for password "
            "recovery, so make sure it's an address you actually check."
        ),
    },
    {
        'match': ['change my height', 'change my weight', 'change my age', 'update body stats',
                  'body stats', 'change profile', 'edit profile'],
        'a': (
            "Body stats (age, height in feet, weight in kg, body type, focus area) live in "
            "**Settings** (`/users/settings/`) → **Fitness profile**. Or open "
            "`/users/profile/edit/` for a single form. These numbers feed your BMR/TDEE and "
            "your diet macro targets, so keep them current."
        ),
    },
    {
        'match': ['buy something', 'order something', 'shop', 'browse products',
                  'find products'],
        'a': (
            "Open the **Store** (`/store/`) to browse by category, or use **All products** "
            "(`/store/products/`) to search and filter. Click any product for full details, "
            "then hit **Add to Cart**. The cart lives at `/store/cart/`. Free shipping kicks "
            "in at NRS 5000."
        ),
    },
    {
        'match': ['see my orders', 'order history', 'track an order', 'where is my order',
                  'check my order'],
        'a': (
            "Open **My Orders** (`/store/orders/`). Each card shows the order number, date, "
            "status, item thumbnails, and total. Click any order to see the full breakdown: "
            "items, shipping address, payment method, payment status, and a tracker bar."
        ),
    },
    {
        'match': ['delete my account', 'close my account', 'remove my account'],
        'a': (
            "Account deletion isn't exposed in the app yet. For now, contact the team at "
            "suwalunish123@gmail.com or sagarshahi865@gmail.com and they'll handle it."
        ),
    },
    {
        'match': ['sign out', 'log out', 'logout'],
        'a': (
            "Click **Logout** in the top-right of the nav. Or open `/users/logout/` directly. "
            "After logging out you can browse the public pages, but you'll need to sign back "
            "in to log workouts, see your records, or place orders."
        ),
    },
    {
        'match': ['create an account', 'how to register', 'how do i register', 'how do i sign up',
                  'i want to sign up', 'i want to register', 'make an account', 'create a profile'],
        'a': (
            "Open **Register** (`/users/register/`). Fill in your username, email, password, "
            "age, height (ft), weight (kg), and primary goal. Submit and you'll be logged in "
            "automatically. Then set your focus area in `/goals/` and pick your first workout "
            "from `/exercises/`."
        ),
    },
    {
        'match': ['how to login', 'how do i login', 'how do i sign in', 'how to sign in',
                  "can't login", "can't sign in", "forgot my password"],
        'a': (
            "Open **Login** (`/users/login/`). Enter your username (case doesn't matter — "
            "'JOHN', 'John', and 'john' all work) and password. Click **Log in**. If you're "
            "stuck, check the 'Trouble signing in?' tips on the login page for common issues "
            "like Caps Lock or incorrect username casing."
        ),
    },
    {
        'match': ['find exercises', 'browse exercises', 'view all exercises', 'see all exercises',
                  'list exercises', 'how do i find a workout', 'how do i browse workouts'],
        'a': (
            "Open **Workout Library** (`/exercises/`). All 36 exercises are listed with "
            "their category, goal, difficulty, and equipment. Click any exercise to see full "
            "details, form tips, and log options. Use the goal-based filter or muscle group "
            "tabs to narrow it down."
        ),
    },
    {
        'match': ['filter exercises', 'exercises by category', 'exercises by goal',
                  'exercises by difficulty', 'how do i filter', 'find exercises for',
                  'exercises for chest', 'exercises for back', 'exercises for legs'],
        'a': (
            "In **Workout Library** (`/exercises/`), use the goal-based filter or muscle group "
            "tabs to narrow exercises. You can ask me directly: say 'show me chest exercises' "
            "or 'what exercises for strength?' and I'll filter them for you."
        ),
    },
    {
        'match': ['exercise details', 'exercise page', 'how to do an exercise', 'view exercise',
                  'open exercise', 'how do i see exercise info', 'exercise form tips'],
        'a': (
            "Click any exercise in the **Workout Library** (`/exercises/`) to open its detail "
            "page. You'll see the full description, target muscles, equipment, working sets/reps, "
            "form tips, common mistakes, breathing cues, safety notes, and a video link if "
            "available. From there you can log it."
        ),
    },
    {
        'match': ['create a goal', 'add a goal', 'make a goal'],
        'a': (
            "Open **Goals** (`/goals/`), click the **Create Goal** button. Pick a focus area "
            "(strength, hypertrophy, endurance, mobility, flexibility, or weight loss), set "
            "your target (e.g. 'bench 100 kg'), and save. Your new goal appears on the goals "
            "page and the Dashboard."
        ),
    },
    {
        'match': ['edit my goal', 'edit goal', 'change my goal details', 'modify goal',
                  'update goal target'],
        'a': (
            "Open **Goals** (`/goals/`), find the goal card you want to change, and click "
            "**Edit**. Update the target, focus area, or both, then save. You can't change "
            "the focus area if that goal is your active profile goal — change that in "
            "**Settings** → **Fitness profile** instead."
        ),
    },
    {
        'match': ['delete a goal', 'remove a goal', 'delete goal', 'remove goal'],
        'a': (
            "Open **Goals** (`/goals/`), find the goal card, and click **Delete**. Confirm "
            "the deletion. The goal and its progress are removed. You can always create a "
            "new one."
        ),
    },
    {
        'match': ['log with details', 'log details', 'log reps', 'log with notes'],
        'a': (
            "Open any exercise in the **Workout Library** (`/exercises/<slug>/`), click "
            "**Log With Details**, and fill in your actual reps, hold time (for planks/isometrics), "
            "and any notes. This gives you a richer record than the quick one-tap log."
        ),
    },
    {
        'match': ['edit a log', 'edit a completion', 'delete a log', 'delete a completion',
                  'edit my record', 'delete my record', 'change a logged exercise'],
        'a': (
            "Open **Progress** (`/progress/`). Find the logged exercise you want to change, "
            "and click **Edit** or **Delete**. Edit lets you update reps, duration, and notes; "
            "Delete removes the entry entirely. You can also find your records at "
            "`/users/records/`."
        ),
    },
    {
        'match': ['meal suggestion', 'personalised meal plan', 'see my meal plan',
                  'get meal suggestion', 'diet suggest page'],
        'a': (
            "Open **Diet Planner** → **Suggest** (`/diet/suggest/`). You'll see your BMR, "
            "TDEE, calorie target, and macro split (protein, carbs, fat) calculated from your "
            "body stats and active goal. Below that are suggested breakfast, lunch, dinner, "
            "and snack options with full macros."
        ),
    },
    {
        'match': ['browse foods', 'food list', 'food database', 'nutrition data', 'look up food',
                  'check food macros', 'find food nutrition'],
        'a': (
            "Open **Diet Planner** → **Foods** (`/diet/foods/`). Browse common foods with "
            "their calorie, protein, carb, and fat profiles. Click a serving size to add it "
            "to a running meal card on the right — totals update live."
        ),
    },
    {
        'match': ['budget meals page', 'affordable meal ideas', 'budget food ideas',
                  'cheap meal options', 'low cost meals'],
        'a': (
            "Open **Diet Planner** → **Budget Meals** (`/diet/budget-meals/`). Pre-planned "
            "affordable meals like oats, eggs, beans, rice, chicken thigh, and frozen veg — "
            "each with full macros and estimated cost. Eating well on a budget is doable."
        ),
    },
    {
        'match': ['add a meal', 'add nutrition record', 'log what i ate', 'record a meal',
                  'add food record', 'log my food', 'log my calories'],
        'a': (
            "Open **Diet Planner** → **Add Record** (`/diet/create/`). Pick meal type "
            "(breakfast, lunch, dinner, snack), add food items and portions, then save. "
            "Your records appear on the main Diet page and help track your daily targets."
        ),
    },
    {
        'match': ['edit a meal', 'edit nutrition record', 'delete a meal', 'delete nutrition record',
                  'change a food record', 'remove a meal log'],
        'a': (
            "Open **Diet Planner** (`/diet/`). Find the meal record you want to change and "
            "click **Edit** or **Delete**. Edit lets you update meal type, food items, and "
            "portions; Delete removes the entry."
        ),
    },
    {
        'match': ['search products', 'filter products', 'sort products', 'search store',
                  'find a product in the store', 'store search'],
        'a': (
            "Open **Store** → **All Products** (`/store/products/`). Use the search bar to "
            "find items by name, sort by price or rating, or filter by category. Each product "
            "card shows price, rating, and an **Add to Cart** button."
        ),
    },
    {
        'match': ['product details', 'product info', 'see product', 'read about product',
                  'view product', 'store product page'],
        'a': (
            "Open **Store** → **All Products** (`/store/products/`), then click any product "
            "to open its detail page. You'll see the full description, price in NRS, rating, "
            "stock status, category, and an **Add to Cart** button. From there you can also "
            "jump to your cart or My Orders."
        ),
    },
    {
        'match': ['order details', 'order breakdown', 'see my order', 'my order status',
                  'track order status', 'view my order'],
        'a': (
            "Open **My Orders** (`/store/orders/`), then click the order you want to inspect. "
            "The order detail page shows every item with thumbnails, your shipping address, "
            "payment method, payment status, and a status tracker bar from Confirmed to Delivered."
        ),
    },
    {
        'match': ['view inspiration', 'see inspiration', 'inspiration page', 'daily quote',
                  'get inspired', 'motivational page'],
        'a': (
            "Open **Inspiration** (`/inspiration/`) for a daily motivational quote, athlete "
            "profiles, training principles, and curated videos. Great for days when you need "
            "a mental boost. Also check **Quotes** (`/inspiration/quotes/`) for a full wall "
            "of motivational quotes."
        ),
    },
    {
        'match': ['athlete icons', 'athlete profiles', 'sport icons', 'fitness icons',
                  'browse icons', 'inspiration athletes', 'famous athletes'],
        'a': (
            "Open **Inspiration** → **Icons** (`/inspiration/icons/`). Profiles of 13 iconic "
            "athletes from various sports. Click any profile to read their full story, quote, "
            "achievements, and training philosophy."
        ),
    },
    {
        'match': ['view quotes', 'all quotes', 'quote wall', 'famous quotes', 'motivational quotes',
                  'see all quotes', 'quotes page'],
        'a': (
            "Open **Inspiration** → **Quotes** (`/inspiration/quotes/`). A full scrollable "
            "wall of motivational fitness quotes. The main Inspiration page also shows one "
            "random quote per visit."
        ),
    },
    {
        'match': ['player hub', 'play page', 'gamification page', 'my level page',
                  'open player hub', 'play dashboard'],
        'a': (
            "Open **Player Hub** (`/play/`). Your gamification dashboard shows your level, "
            "XP, coins, streak shields, today's daily quests, and recently unlocked badges. "
            "From here navigate to Badges, Quests, or the Leaderboard."
        ),
    },
    {
        'match': ['view badges', 'badge list', 'my badges', 'unlock badges', 'see my badges',
                  'view all badges', 'how to earn badges'],
        'a': (
            "Open **Play** → **Badges** (`/play/badges/`). All 17 badges are organised by "
            "tier: Bronze, Silver, Gold, Diamond. Unlocked badges glow with their tier colour; "
            "locked ones show a hint about how to earn them (e.g. 'log 7 workouts in a week' "
            "for Week Warrior)."
        ),
    },
    {
        'match': ['view quests', 'quest board', 'my quests', 'claim quest', 'how to claim',
                  'claim reward', 'daily challenges', 'how do i complete quests'],
        'a': (
            "Open **Play** → **Quests** (`/play/quests/`). Active daily and weekly quests are "
            "shown with progress bars (e.g. '3/5 workouts logged'). When a quest is complete, "
            "hit **Claim** to earn XP and coins. Use **Re-roll** to swap a quest you don't "
            "want. Level-up and badge announcements pop up automatically when you claim."
        ),
    },
    {
        'match': ['view leaderboard', 'leaderboard page', 'top players', 'my ranking',
                  'see leaderboard', 'scoreboard', 'how do i rank'],
        'a': (
            "Open **Play** → **Leaderboard** (`/play/leaderboard/`). All members ranked by "
            "total XP. Your row lights up so you can find yourself easily. There's also a "
            "streak leaderboard for the most consistent trainers. Titles: Rookie → Beast → "
            "Monster → Immortal → Transcendent."
        ),
    },
    {
        'match': ['how to earn xp', 'earn experience', 'how do i level up', 'gain xp',
                  'get more xp', 'how to level up', 'increase my level'],
        'a': (
            "You earn XP by doing what you already do:\n"
            "• **Log workouts** — every exercise completion gives XP\n"
            "• **Complete goals** — finishing a goal awards bonus XP\n"
            "• **Log meals** — recording nutrition earns XP\n"
            "• **Buy from the store** — placing an order gives XP\n"
            "• **Complete quests** — daily and weekly quests give bonus XP and coins\n\n"
            "Your level and title (Rookie → Beast → Monster → Immortal → Transcendent) "
            "progress automatically as XP accumulates. Open `/play/` to see your current stats."
        ),
    },
    {
        'match': ['change my focus', 'change activity level', 'change body type',
                  'update goal focus', 'change focus area'],
        'a': (
            "Open **Settings** (`/users/settings/`) → **Fitness profile**. You can change "
            "your activity level (sedentary, light, moderate, very active), body type "
            "(ectomorph, mesomorph, endomorph), and focus area. These values update your "
            "BMR/TDEE calculations and exercise recommendations."
        ),
    },
    {
        'match': ['how to use the chatbot', 'use the coach', 'how to talk to coach',
                  'chat with coach', 'how do i ask', 'talk to the bot'],
        'a': (
            "You're already talking to me! I'm the Fitness Hub bot. Just "
            "type your question in the chat box below. I can help with exercise technique, "
            "app navigation, diet & nutrition, supplements, sleep, recovery, motivation, and "
            "more. I'm read-only — I never change your account data."
        ),
    },
]


def find_howto(text: str):
    """Return the how-to answer if a known question matches."""
    t = (text or '').lower()
    for entry in APP_HOWTO:
        for needle in entry['match']:
            if needle in t:
                return entry['a']
    return None


def find_faq_answer(text: str):
    t = (text or '').lower()
    for entry in NUTRITION_FAQ + GENERAL_FITNESS_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Exercise encyclopedia — cues, form tips, common mistakes by muscle group.
# Used when the user asks "how do I do X" or "form for X" at a category level.
# Individual exercises have their own data in the DB; this is the fallback.
# ---------------------------------------------------------------------------

EXERCISE_ENCYCLOPEDIA = {
    'chest': {
        'title': 'Chest training',
        'cues': (
            "**Pushing cues:**\n"
            "• Pinch your shoulder blades back and down before you press — don't let them shrug up.\n"
            "• Lower with control to a deep, comfortable stretch. No bouncing.\n"
            "• Drive the bar/bell up and slightly back toward the rack, not straight up at the ceiling.\n"
            "• Breathe: inhale on the way down, brace at the bottom, exhale as you press up."
        ),
        'mistakes': (
            "**Common chest mistakes:**\n"
            "• Flaring the elbows to 90°+ on bench — keep them ~45–60° to save your shoulders.\n"
            "• Bouncing the bar off the chest. Lower with control, press with intent.\n"
            "• Half-repping — go to a real stretch, then a real lockout (or near it).\n"
            "• Letting the lower back hyperextend on bench — feet flat, ribcage down, glutes on the bench."
        ),
        'keywords': ['chest', 'pec', 'pecs', 'bench', 'push-up', 'pushup', 'press', 'fly'],
    },
    'back': {
        'title': 'Back training',
        'cues': (
            "**Pulling cues:**\n"
            "• Lead with the elbows, not the hands — 'elbows to your back pockets.'\n"
            "• Squeeze the shoulder blades together at the end of every rep. Pause for a beat.\n"
            "• Keep the neck neutral — don't crank the head forward to meet the bar.\n"
            "• Use a full range: stretch at the top, contract hard at the bottom."
        ),
        'mistakes': (
            "**Common back mistakes:**\n"
            "• Yanking with the arms instead of pulling with the back. The arms are just hooks.\n"
            "• Rounded lower back under heavy load — brace the abs, neutral spine.\n"
            "• Half-repping rows — chest to bar, then full extension at the bottom.\n"
            "• Shrugging the shoulders up to the ears on pulldowns. Drive elbows down, traps relaxed."
        ),
        'keywords': ['back', 'lat', 'lats', 'pull-up', 'pullup', 'row', 'pulldown', 'pull'],
    },
    'shoulders': {
        'title': 'Shoulder training',
        'cues': (
            "**Overhead & lateral cues:**\n"
            "• Lateral raises: lead with the elbows, not the hands. Pinkies slightly up.\n"
            "• Overhead press: glutes tight, ribs down, press the bar in a straight line over the mid-foot.\n"
            "• Face pulls: externally rotate at the end (think 'showing your biceps to the wall in front of you').\n"
            "• Keep the traps out of it — they're not the prime mover on laterals."
        ),
        'mistakes': (
            "**Common shoulder mistakes:**\n"
            "• Shrugging on lateral raises — the goal is delts, not traps.\n"
            "• Over-arching the lower back on overhead press — squeeze the glutes and brace.\n"
            "• Locking out aggressively on press — leave a small bend in the elbow.\n"
            "• Using momentum to swing the weight up. Slow down, feel the muscle."
        ),
        'keywords': ['shoulder', 'delt', 'delts', 'press', 'raise', 'lateral', 'overhead', 'face pull'],
    },
    'arms': {
        'title': 'Arm training',
        'cues': (
            "**Biceps & triceps cues:**\n"
            "• Curls: pin the elbows to your sides, don't swing. Full stretch at the bottom, hard squeeze at the top.\n"
            "• Triceps: lock the shoulders down, full extension at the bottom, slow eccentric.\n"
            "• Slow eccentrics (3 seconds down) on curls are an easy growth hack.\n"
            "• Supinate (turn palm up) on curls for full bicep involvement."
        ),
        'mistakes': (
            "**Common arm mistakes:**\n"
            "• Cheat-curl the weight up and call it a rep. The bicep didn't do the work.\n"
            "• Let the elbows drift forward on curls. They stay pinned.\n"
            "• Skipping triceps — they're ~⅔ of the upper arm. Don't neglect them.\n"
            "• Doing 8 exercises for arms and 0 for legs. We see you."
        ),
        'keywords': ['arm', 'arms', 'bicep', 'biceps', 'tricep', 'triceps', 'curl', 'forearm'],
    },
    'legs': {
        'title': 'Leg training',
        'cues': (
            "**Squat & hinge cues:**\n"
            "• Squat: knees track over toes, weight in mid-foot, chest tall, hips back.\n"
            "• Hinge (deadlift/RDL): push the hips back, soft knee, bar glides along the legs.\n"
            "• Lunge: step out, drop the back knee, front knee tracks over the front foot.\n"
            "• Brace your core like someone is about to punch your stomach. Every. Single. Rep."
        ),
        'mistakes': (
            "**Common leg mistakes:**\n"
            "• Knees caving inward on squat — drive them out, especially in the hole.\n"
            "• Rounding the lower back on deadlift — keep it neutral, hinge from the hips.\n"
            "• Half-squatting and calling it depth. Go to a parallel or below that you actually own.\n"
            "• Skipping legs entirely. Cardio doesn't build quads. Squats do."
        ),
        'keywords': ['leg', 'legs', 'quad', 'quads', 'hamstring', 'glute', 'glutes', 'calf', 'calves',
                     'squat', 'deadlift', 'lunge', 'rdl', 'hip thrust'],
    },
    'core': {
        'title': 'Core training',
        'cues': (
            "**Core cues:**\n"
            "• Brace 360° — abs, sides, lower back, glutes. Imagine bracing for a punch.\n"
            "• Hollow body position: ribcage down, lower back pressed to the floor (or close).\n"
            "• Slow, controlled reps. No swinging, no jerking.\n"
            "• Breathe through the rep. Holding your breath forever is for max lifts, not ab work."
        ),
        'mistakes': (
            "**Common core mistakes:**\n"
            "• Cranking the neck during crunches. Hands behind the head for support, not pulling.\n"
            "• Using only sit-ups. Anti-rotation (Pallof press) and anti-extension (planks) matter more for real-world strength.\n"
            "• Holding the breath forever. Breathe.\n"
            "• Crunching 1000 reps a day. Abs grow from progressive overload like every other muscle."
        ),
        'keywords': ['core', 'abs', 'abdominal', 'oblique', 'obliques', 'plank', 'crunch', 'sit-up'],
    },
    'cardio': {
        'title': 'Cardio training',
        'cues': (
            "**Cardio cues:**\n"
            "• Pick a mode you actually like — running, biking, rowing, jump rope, swimming.\n"
            "• Heart rate zones: Z1 (easy, can talk) for recovery, Z2 (brisk, full sentences) for base, Z3+ (hard) for intervals.\n"
            "• Mix steady-state and intervals. Both have value; both work for different goals.\n"
            "• Warm up 5 min easy, do your work, cool down 5 min easy. Skipping the cool-down is how people get dizzy."
        ),
        'mistakes': (
            "**Common cardio mistakes:**\n"
            "• Doing only slow steady-state, never pushing. Your heart has more than one gear.\n"
            "• Going 100% every session. Easy days build the aerobic base. Hard days go hard.\n"
            "• Doing 90 min of cardio to 'make up for' 20 min of bad eating. Math doesn't work that way.\n"
            "• Skipping the cool-down. Your heart deserves a cool-down."
        ),
        'keywords': ['cardio', 'run', 'running', 'jog', 'walk', 'walk', 'bike', 'cycling', 'swim',
                     'rowing', 'jump rope', 'hiit', 'liss'],
    },
}


def find_encyclopedia_entry(text: str):
    """Return (key, entry) for the muscle group mentioned in text, or (None, None)."""
    import re
    t = (text or '').lower()
    for key, entry in EXERCISE_ENCYCLOPEDIA.items():
        for kw in entry['keywords']:
            if re.search(r'\b' + re.escape(kw) + r'\b', t):
                return key, entry
    return None, None


def encyclopedia_reply(text: str) -> str | None:
    """Return a category-level exercise encyclopedia reply if the text mentions a muscle group."""
    key, entry = find_encyclopedia_entry(text)
    if not entry:
        return None
    return (
        f"**{entry['title']} — form cues:**\n\n{entry['cues']}\n\n"
        f"{entry['mistakes']}\n\n"
        f"Open the Workout Library at `/exercises/` and filter by "
        f"**{entry['title'].split()[0].lower()}** to see the full list of exercises with details."
    )


# ---------------------------------------------------------------------------
# Training principles — programming, RPE, volume, frequency, deload, splits.
# ---------------------------------------------------------------------------

TRAINING_PRINCIPLES = [
    {
        'match': ['progressive overload', 'how do i progress', 'how to get stronger',
                  'how to progress', 'progress overload'],
        'a': (
            "**Progressive overload** just means doing a little more over time:\n"
            "• Add 1 rep per set, then add weight once you hit the top of the rep range.\n"
            "• Add a set (e.g. 3 → 4 working sets).\n"
            "• Improve form / range of motion on the same weight.\n"
            "• Reduce rest time between sets for the same weight.\n\n"
            "The point: beat yesterday by a small, repeatable amount. That's the whole game."
        ),
    },
    {
        'match': ['rpe', 'rate of perceived', 'how hard should i go', 'intensity scale',
                  'how heavy', 'what weight should i use'],
        'a': (
            "**RPE (Rate of Perceived Exertion) is your intensity dial:**\n"
            "• **RPE 10** — absolute max, 0 reps left in the tank.\n"
            "• **RPE 9** — could maybe do 1 more rep.\n"
            "• **RPE 8** — 2 reps left. The sweet spot for most working sets.\n"
            "• **RPE 7** — 3 reps left. Good for volume work.\n"
            "• **RPE 5–6** — easy, conversational. Great for warm-ups and technique.\n\n"
            "For hypertrophy, most working sets should sit around RPE 7–9. For strength, lean 8–9.5."
        ),
    },
    {
        'match': ['volume', 'how many sets', 'sets per week', 'volume per muscle',
                  'how many sets per muscle'],
        'a': (
            "**Volume (the weekly set count per muscle) is the main driver of growth:**\n"
            "• **Minimum effective:** ~6–8 hard sets per muscle per week.\n"
            "• **Optimal range:** ~10–20 sets per muscle per week.\n"
            "• **Diminishing returns:** above ~20–25 sets, recovery cost > benefit.\n\n"
            "Start at the low end. Add sets every few weeks. If you're recovering, push it up. "
            "If you're beat up, pull it back. The body gives you feedback — listen to it."
        ),
    },
    {
        'match': ['how often train', 'frequency', 'how many days a week', 'training frequency',
                  'times a week', 'days per week'],
        'a': (
            "**Training frequency** is how often you hit a muscle per week:\n"
            "• **1x/week per muscle** — works for beginners, not optimal long-term.\n"
            "• **2x/week per muscle** — the current best-practice sweet spot for most people.\n"
            "• **3x+/week per muscle** — useful for advanced lifters, but recovery cost adds up fast.\n\n"
            "A 3-day full-body program trains each muscle 3x/week. A 4-day upper/lower trains "
            "each muscle 2x/week. Both are good. Pick the one you'll actually do."
        ),
    },
    {
        'match': ['split', 'upper lower', 'push pull legs', 'full body', 'ppl', 'bro split',
                  'training split', 'what split'],
        'a': (
            "**Common splits, ranked by experience:**\n"
            "• **Full-body (3x/week)** — beginner favorite, hits each muscle 3x/week, simple.\n"
            "• **Upper/Lower (4x/week)** — solid step up. Each muscle 2x/week.\n"
            "• **Push/Pull/Legs (3 or 6 days)** — popular, flexible.\n"
            "• **Bro split (1 muscle/day)** — fine for bodybuilders, but not the most efficient use of your time.\n\n"
            "Best split = the one you'll execute consistently for months. The program only "
            "matters if you actually do it."
        ),
    },
    {
        'match': ['deload', 'recovery week', 'i am burnt out', 'overtraining', 'i feel beat up',
                  'tired all the time', 'rest week'],
        'a': (
            "**Deload weeks** are scheduled recovery:\n"
            "• Drop volume by ~40–50% (e.g. 5 sets → 2–3 sets).\n"
            "• OR drop intensity (RPE 9 → RPE 6) at the same volume.\n"
            "• Keep frequency, keep movement patterns, just less of them.\n"
            "• Every 4–6 weeks of hard training, take a deload. It's not weakness — it's programming.\n\n"
            "You don't grow in the workout. You grow during recovery. The deload is when "
            "you actually get stronger."
        ),
    },
    {
        'match': ['1rm', 'one rep max', 'max', 'how much can i lift', 'estimated max'],
        'a': (
            "**Estimated 1RM** from a working set:\n"
            "• 5 reps → ~85% of 1RM\n"
            "• 8 reps → ~80% of 1RM\n"
            "• 10 reps → ~75% of 1RM\n\n"
            "**Epley formula:** 1RM ≈ weight × (1 + reps/30).\n\n"
            "Don't test your true 1RM often. Train in the 5–8 rep range most of the time and "
            "let the math estimate the rest."
        ),
    },
    {
        'match': ['rep range', 'how many reps', 'sets and reps', 'rep scheme', 'how many reps should i do'],
        'a': (
            "**Rep ranges by goal:**\n"
            "• **Strength** — 1–5 reps, heavy, long rest (3–5 min).\n"
            "• **Hypertrophy (growth)** — 6–12 reps, moderate, 60–90s rest.\n"
            "• **Endurance** — 12–20+ reps, light, 30–60s rest.\n"
            "• **Power** — 3–5 reps explosive, long rest.\n\n"
            "Most people do well with a mix. Don't get religious about rep ranges — they're "
            "guidelines, not commandments."
        ),
    },
]


def find_principle(text: str):
    t = (text or '').lower()
    for entry in TRAINING_PRINCIPLES:
        for needle in entry['match']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Cardio deep dive — HIIT, LISS, zones.
# ---------------------------------------------------------------------------

CARDIO_FAQ = [
    {
        'q': ['what is hiit', 'hiit', 'high intensity', 'interval training'],
        'a': (
            "**HIIT (High-Intensity Interval Training):**\n"
            "• Short bursts of near-max effort (20–60 sec), then equal or longer recovery (40–120 sec).\n"
            "• Total session: 15–25 minutes. Effective, time-efficient.\n"
            "• Examples: 8×30s sprint / 60s walk, or 4×4 min hard / 3 min easy.\n"
            "• Calorie burn during + after-effect (EPOC) is high.\n"
            "• Don't do HIIT every day. 1–3x/week is plenty; pair it with easier cardio on other days."
        ),
    },
    {
        'q': ['what is liss', 'liss', 'low intensity', 'steady state', 'zone 2', 'zone 2 training'],
        'a': (
            "**LISS (Low-Intensity Steady State) / Zone 2 cardio:**\n"
            "• Easy pace where you can hold a conversation in full sentences.\n"
            "• Builds the aerobic base, burns fat for fuel, low recovery cost.\n"
            "• 30–60 minutes, 2–4x/week is a solid base.\n"
            "• Heart rate: roughly 60–70% of your max.\n"
            "• Most 'cardio' people should be doing is Zone 2. Boring, but powerful over time."
        ),
    },
    {
        'q': ['how to run', 'start running', 'running tips', 'couch to 5k', 'beginner running'],
        'a': (
            "**Beginner running, in plain steps:**\n"
            "1. Walk briskly for 5 min to warm up.\n"
            "2. Run easy for 60 sec, walk 90 sec. Repeat 6–8 times.\n"
            "3. Cool down with 5 min walking.\n"
            "4. Add 1 more run/walk interval every week.\n"
            "5. After ~6–8 weeks, you'll be running 20–30 min continuously.\n\n"
            "Don't skip the walk breaks — they're training, not failure. "
            "Run easy enough that you can talk. Speed comes later."
        ),
    },
    {
        'q': ['best cardio', 'what cardio should i do', 'cardio for fat loss',
              'cardio to lose weight'],
        'a': (
            "**The best cardio is the one you'll do consistently.**\n"
            "• Most people: mix of Zone 2 (2–3x/week) + 1 HIIT session/week.\n"
            "• For fat loss: cardio helps, but diet is the bigger lever.\n"
            "• For heart health: any sustained elevated heart rate, 150+ min/week.\n"
            "• Pick a mode you enjoy: running, biking, rowing, jump rope, swimming, hiking, "
            "dancing — they all count."
        ),
    },
]


def find_cardio_answer(text: str):
    t = (text or '').lower()
    for entry in CARDIO_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Stretching & mobility
# ---------------------------------------------------------------------------

MOBILITY_FAQ = [
    {
        'q': ['stretching', 'stretch', 'when to stretch', 'should i stretch'],
        'a': (
            "**Stretching — the practical version:**\n"
            "• **Dynamic stretching** (arm circles, leg swings) before training. Warm-up.\n"
            "• **Static stretching** (hold a position 20–30 sec) after training or on rest days.\n"
            "• Heavy static stretching before heavy lifting can briefly reduce force production, "
            "so save the long holds for after the workout.\n"
            "• 5–10 minutes of mobility work daily is enough to maintain range of motion."
        ),
    },
    {
        'q': ['mobility', 'stiff', 'tight hips', 'tight shoulders', 'range of motion'],
        'a': (
            "**Mobility basics — fix the most common stiff spots:**\n"
            "• **Hips:** 90/90 hip rotations, deep squat hold, couch stretch.\n"
            "• **Shoulders:** wall slides, dead hangs, thoracic spine rotations.\n"
            "• **Thoracic spine:** cat-cow, open-book stretch, foam roller extensions.\n"
            "• **Ankles:** calf stretches, ankle circles — important for squat depth.\n\n"
            "Do a 5-min mobility flow every day. Consistency > intensity. "
            "Most people improve range of motion in 2–4 weeks."
        ),
    },
    {
        'q': ['cool down', 'post workout stretch'],
        'a': (
            "**Cool-down (5 min, easy):**\n"
            "• 2–3 min easy cardio (walk, slow bike) to bring the heart rate down.\n"
            "• 2–3 min static stretching on what you trained — chest, back, legs, whatever.\n"
            "• Optional: foam roll the tight spots for 1–2 min each.\n\n"
            "Cooling down doesn't 'flush lactic acid' (that's a myth), but it does help "
            "you feel less stiff the next day."
        ),
    },
]


def find_mobility_answer(text: str):
    t = (text or '').lower()
    for entry in MOBILITY_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Sleep & recovery
# ---------------------------------------------------------------------------

SLEEP_RECOVERY_FAQ = [
    {
        'q': ['how much sleep', 'sleep for muscle', 'sleep for training', 'how many hours sleep',
              'sleep tips'],
        'a': (
            "**Sleep is the cheat code:**\n"
            "• **7–9 hours** per night is the evidence-based range for most adults.\n"
            "• Athletes and people in hard training blocks often do best at 8–9 hours.\n"
            "• Poor sleep = worse recovery, higher injury risk, more hunger, less progress.\n"
            "• Practical tips: dark room, cool temperature, no screens 30 min before bed, "
            "consistent wake time even on weekends."
        ),
    },
    {
        'q': ['soreness', 'sore', 'doms', 'delayed onset'],
        'a': (
            "**DOMS (Delayed Onset Muscle Soreness):**\n"
            "• Normal 24–72 hours after a new or hard training session.\n"
            "• Light movement (walk, easy bike) and sleep help more than anything else.\n"
            "• Cold water immersion can help short-term but may slightly blunt adaptations — "
            "use it sparingly.\n"
            "• Sharp or sudden pain during a lift is NOT soreness. Stop."
        ),
    },
    {
        'q': ['active recovery', 'rest day', 'what to do on rest day', 'off day'],
        'a': (
            "**Rest day = recovery day. Make it active:**\n"
            "• 20–30 min easy walk, light bike, or mobility flow.\n"
            "• Light stretching or foam rolling.\n"
            "• Sleep a little extra.\n"
            "• Eat normal meals — don't under-eat on rest days. Your body is repairing.\n\n"
            "Rest is when adaptation happens. The training session is the stimulus, "
            "the rest day is the response."
        ),
    },
]


def find_sleep_recovery_answer(text: str):
    t = (text or '').lower()
    for entry in SLEEP_RECOVERY_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Legal, evidence-based supplements (no prohibited substances)
# ---------------------------------------------------------------------------

SUPPLEMENT_FAQ = [
    {
        'q': ['creatine', 'should i take creatine', 'creatine monohydrate'],
        'a': (
            "**Creatine monohydrate** — the most studied, safest, most effective legal "
            "supplement in sports nutrition.\n"
            "• Dose: 3–5 g per day, every day. Loading is optional.\n"
            "• Timing: any time of day. Consistency matters more than timing.\n"
            "• Effects: +1–2 reps on heavy sets, better recovery, slight muscle fullness.\n"
            "• Safe for healthy adults. Drink enough water. Skip if you have kidney issues — "
            "check with your doctor."
        ),
    },
    {
        'q': ['whey', 'whey protein', 'protein powder', 'should i use protein powder'],
        'a': (
            "**Whey / protein powder** — it's just food in powder form:\n"
            "• Use it to hit your daily protein target if whole food is hard.\n"
            "• 1 scoop ≈ 20–25 g protein. Mix with water, milk, oats, or smoothies.\n"
            "• Whey, casein, plant (pea, soy) — all fine. Pick one you tolerate and like.\n"
            "• Don't rely on it as your only protein source. Real food still matters."
        ),
    },
    {
        'q': ['caffeine', 'pre workout', 'coffee', 'should i drink coffee before'],
        'a': (
            "**Caffeine** — the most evidence-backed legal pre-workout:\n"
            "• 3–6 mg per kg of bodyweight, ~30–60 min before training.\n"
            "• Coffee, tea, or any cheap caffeine pill works. Pre-workout powders are just "
            "expensive caffeine with flavor.\n"
            "• Avoid within ~6 hours of bed if it disrupts your sleep.\n"
            "• Tolerance builds fast. Cycle off for 1–2 weeks every couple months."
        ),
    },
    {
        'q': ['electrolytes', 'salt', 'potassium', 'magnesium'],
        'a': (
            "**Electrolytes** — important if you sweat a lot:\n"
            "• Sodium: most people undersalt. Add a pinch of salt to water on heavy sweat days.\n"
            "• Potassium: bananas, potatoes, coconut water — whole foods cover most needs.\n"
            "• Magnesium: 200–400 mg before bed can help sleep and muscle cramps.\n"
            "• Most 'fancy' electrolyte drinks are mostly flavored salt water. Make your own."
        ),
    },
    {
        'q': ['multivitamin', 'vitamin d', 'fish oil', 'omega 3'],
        'a': (
            "**Other evidence-backed basics:**\n"
            "• **Vitamin D** — 1000–2000 IU/day, especially if you live somewhere with "
            "limited sun. Get bloodwork if you can.\n"
            "• **Omega-3 (fish oil)** — 1–3 g/day with food. Anti-inflammatory, heart health.\n"
            "• **Magnesium** — 200–400 mg before bed. Helps sleep and recovery.\n"
            "• **Multivitamin** — fine as insurance, not a replacement for a real diet."
        ),
    },
    {
        'q': ['supplement', 'what supplements', 'supplements to take',
              'which supplements work'],
        'a': (
            "**If you only do three things, do these:**\n"
            "1. **Creatine monohydrate** — 3–5 g/day. Cheap, legal, evidence-based.\n"
            "2. **Vitamin D** — 1000–2000 IU/day, especially with limited sun.\n"
            "3. **Protein source** — whey, food, or both. Hit your daily protein target.\n\n"
            "Everything else is bonus. The boring stack is the effective stack."
        ),
    },
]


def find_supplement_answer(text: str):
    t = (text or '').lower()
    for entry in SUPPLEMENT_FAQ:
        for needle in entry['q']:
            if needle in t:
                return entry['a']
    return None


# ---------------------------------------------------------------------------
# Master lookup — try every knowledge source in order.
# ---------------------------------------------------------------------------

def find_any_knowledge(text: str):
    """Run through every knowledge source and return the first match.

    Order matters: more specific → more general.
    """
    if not text:
        return None
    for finder in (
        find_principle,
        find_cardio_answer,
        find_mobility_answer,
        find_sleep_recovery_answer,
        find_supplement_answer,
        find_faq_answer,
        find_howto,
    ):
        result = finder(text)
        if result:
            return result
    return None

