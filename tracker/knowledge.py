"""Curated, source-linked fitness education that does not spend external API quota."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

ARTICLES = [
    {
        "slug": "weekly-activity-basics",
        "title": "The weekly activity baseline",
        "category": "Training basics",
        "read_time": "4 min",
        "summary": "A practical starting point for balancing cardio, strength work and everyday movement.",
        "sections": [
            {"heading": "What the guidelines say", "body": "For generally healthy adults aged 18–64, WHO recommends 150–300 minutes of moderate-intensity aerobic activity each week, or 75–150 minutes of vigorous activity, or an equivalent combination. Adults should also do muscle-strengthening activity involving all major muscle groups on at least two days each week."},
            {"heading": "Make it manageable", "bullets": ["Break activity into sessions that fit your week; it does not all need to happen at once.", "If you are starting from very little activity, begin with an amount you can recover from and build gradually.", "Walking, cycling, sport and gym sessions can all contribute to activity."]},
            {"heading": "Remember", "body": "These are population-level adult guidelines, not a personalised prescription. Some activity is better than none; adapt activity to your ability and circumstances."},
        ],
        "sources": [
            {"label": "WHO — Physical activity", "url": "https://www.who.int/initiatives/behealthy/physical-activity/"},
            {"label": "CDC — Adult activity guidelines", "url": "https://www.cdc.gov/physical-activity-basics/guidelines/adults.html"},
        ],
    },
    {
        "slug": "strength-training-foundations",
        "title": "Strength training: the foundations",
        "category": "Strength",
        "read_time": "5 min",
        "summary": "Understand movement patterns, controlled repetitions and how to start a balanced routine.",
        "sections": [
            {"heading": "Train the whole body", "body": "A balanced strength routine includes movements for the legs, hips, back, abdomen, chest, shoulders and arms. You can organise these as full-body sessions or split them across the week."},
            {"heading": "Prioritise quality", "bullets": ["Choose a load you can control through a comfortable range of motion.", "Use steady repetitions instead of rushing or bouncing through them.", "Stop a set when you cannot maintain safe, consistent technique.", "Record sets, repetitions and load so you can understand what you actually did."]},
            {"heading": "Build consistency first", "body": "A repeatable routine you can recover from is more useful than an intense plan you cannot sustain. Beginners can start with a small number of exercises and gradually learn the movements."},
        ],
        "sources": [
            {"label": "WHO — Physical activity guidelines", "url": "https://www.who.int/initiatives/behealthy/physical-activity/"},
            {"label": "CDC — Adult activity guidelines", "url": "https://www.cdc.gov/physical-activity-basics/guidelines/adults.html"},
        ],
    },
    {
        "slug": "progressive-overload",
        "title": "Progressive overload without guesswork",
        "category": "Programming",
        "read_time": "4 min",
        "summary": "Learn how to make training gradually more challenging while keeping technique in control.",
        "sections": [
            {"heading": "The basic idea", "body": "To keep adapting, training usually needs a gradual and appropriate increase in challenge over time. That can mean adding a small amount of weight, performing an extra repetition, adding a set, improving control or using a more challenging variation."},
            {"heading": "A simple method", "bullets": ["Track the weight and repetitions for each working set.", "Repeat a load until you can complete your planned repetitions with consistent form.", "Change one training variable at a time, in small steps.", "If technique breaks down or recovery suffers, hold steady or reduce the challenge."]},
            {"heading": "Do not chase numbers", "body": "More weight is not automatically better. Pain, shortened range of motion and uncontrolled repetitions are not signs of productive progress."},
        ],
        "sources": [
            {"label": "CDC — Adult activity guidelines", "url": "https://www.cdc.gov/physical-activity-basics/guidelines/adults.html"},
        ],
    },
    {
        "slug": "protein-and-training",
        "title": "Protein and training: what matters",
        "category": "Nutrition",
        "read_time": "5 min",
        "summary": "A research-based overview of protein needs, everyday food and why total intake matters.",
        "sections": [
            {"heading": "A useful research range", "body": "The International Society of Sports Nutrition position stand reports that 1.4–2.0 grams of protein per kilogram of body weight per day is sufficient for most healthy exercising individuals. Needs vary with training, energy intake, body composition and individual circumstances; this range is not a target everyone must reach."},
            {"heading": "Start with food", "bullets": ["Include protein-containing foods across meals, such as lentils, beans, dairy, eggs, soy, fish or meat according to your preferences.", "Look at your overall daily eating pattern rather than relying on a single post-workout shake.", "Supplements are optional conveniences, not a requirement for making progress."]},
            {"heading": "Personal circumstances matter", "body": "People with kidney disease, relevant medical conditions, pregnancy-related needs or other clinical nutrition requirements should seek individual guidance from a qualified health professional before changing protein intake."},
        ],
        "sources": [
            {"label": "ISSN — Protein and exercise (open-access review)", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5477153/"},
        ],
    },
    {
        "slug": "recovery-and-rest",
        "title": "Recovery is part of the programme",
        "category": "Recovery",
        "read_time": "4 min",
        "summary": "Why rest, sleep, food and manageable training volume belong in a good fitness plan.",
        "sections": [
            {"heading": "Training is only one part", "body": "Exercise provides a training stimulus; recovery helps you return ready for future sessions. Harder or longer sessions are not automatically better if they leave you unable to train consistently."},
            {"heading": "Useful habits", "bullets": ["Keep a regular sleep routine and allow enough time for rest.", "Eat enough to support your activity and include a varied range of foods.", "Avoid training the same muscles hard every day; plan easier days where needed.", "Notice persistent fatigue, declining performance or pain and adjust your plan."]},
            {"heading": "When to get help", "body": "Stop exercising and seek appropriate medical advice for concerning symptoms such as chest pain, fainting or unusual severe breathlessness. Persistent or worsening pain deserves assessment rather than being trained through."},
        ],
        "sources": [
            {"label": "WHO — Physical activity and health", "url": "https://www.who.int/initiatives/behealthy/physical-activity/"},
            {"label": "CDC — Benefits of physical activity", "url": "https://www.cdc.gov/physical-activity-basics/benefits/index.html"},
        ],
    },
    {
        "slug": "supplements-reality-check",
        "title": "Supplements: a practical reality check",
        "category": "Nutrition",
        "read_time": "4 min",
        "summary": "Separate useful basics from marketing claims before spending money.",
        "sections": [
            {"heading": "Food and consistency come first", "body": "Supplements cannot replace a suitable training plan, adequate food, sleep and consistency. Many people can meet their nutrition needs through ordinary foods."},
            {"heading": "Before buying anything", "bullets": ["Ask what specific need the product is meant to address.", "Check the ingredient list, dose, safety warnings and independent quality testing where available.", "Be cautious of products promising rapid fat loss, dramatic muscle gain or guaranteed results.", "Consider cost and whether the benefit is supported by good evidence."]},
            {"heading": "Safety matters", "body": "Supplements can interact with medicines and may not be appropriate for everyone. Ask a qualified clinician or dietitian if you have a health condition, take medication or are unsure."},
        ],
        "sources": [
            {"label": "NIH Office of Dietary Supplements", "url": "https://ods.od.nih.gov/"},
        ],
    },
]


@login_required
def learn(request):
    query = " ".join(request.GET.get("q", "").split())[:80]
    category = request.GET.get("category", "").strip()[:30]
    categories = sorted({article["category"] for article in ARTICLES})
    articles = ARTICLES
    if category in categories:
        articles = [article for article in articles if article["category"] == category]
    else:
        category = ""
    if query:
        needle = query.casefold()
        articles = [
            article for article in articles
            if needle in " ".join([
                article["title"], article["category"], article["summary"],
                *(section.get("heading", "") + " " + section.get("body", "") + " " + " ".join(section.get("bullets", []))
                  for section in article["sections"]),
            ]).casefold()
        ]
    return render(request, "tracker/learn.html", {
        "articles": articles,
        "query": query,
        "category": category,
        "categories": categories,
        "result_count": len(articles),
    })
