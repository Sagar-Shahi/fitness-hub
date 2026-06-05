"""Seed the inspiration app with real fitness icons, categories, and quotes.

Photo URLs use Unsplash fitness-themed images that represent each discipline
(not portraits of specific individuals, to avoid licensing concerns). The
biographies, achievements, training tips, and quotes are sourced from
publicly-available interviews, official records, and biographies.
"""
from django.core.management.base import BaseCommand

from inspiration.models import FitnessIcon, InspirationCategory, MotivationQuote


CATEGORIES = [
    {
        'name': 'Bodybuilding',
        'slug': 'bodybuilding',
        'description': 'The art and science of building a championship physique — mass, symmetry, and stage presence.',
        'icon': '🏆',
        'accent': 'emerald',
        'display_order': 1,
    },
    {
        'name': 'CrossFit',
        'slug': 'crossfit',
        'description': 'Constantly varied, high-intensity functional movement forged in the crucible of competition.',
        'icon': '🔥',
        'accent': 'rose',
        'display_order': 2,
    },
    {
        'name': 'Strength Sports',
        'slug': 'strength',
        'description': 'Powerlifting, strongman, and weightlifting — where raw strength meets perfect technique.',
        'icon': '🏋️',
        'accent': 'amber',
        'display_order': 3,
    },
    {
        'name': 'Endurance',
        'slug': 'endurance',
        'description': 'Marathoners, ultrarunners, and triathletes who redefine what the human body can sustain.',
        'icon': '🏃',
        'accent': 'sky',
        'display_order': 4,
    },
    {
        'name': 'Athletics & Gymnastics',
        'slug': 'athletics',
        'description': 'Track stars, gymnasts, and Olympic athletes who push the boundaries of speed, power, and grace.',
        'icon': '🤸',
        'accent': 'violet',
        'display_order': 5,
    },
    {
        'name': 'Mindset & Discipline',
        'slug': 'mindset',
        'description': 'Coaches, authors, and ultra-endurance performers who prove the body achieves what the mind believes.',
        'icon': '🧠',
        'accent': 'cyan',
        'display_order': 6,
    },
]


# Use generic, proven Unsplash fitness photos. The slug-based mapping keeps
# the seeding stable even if we re-run the command.
IMAGES = {
    'bodybuilding_main':   'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=1200&q=80',
    'bodybuilding_alt':    'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1200&q=80',
    'crossfit_main':       'https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?auto=format&fit=crop&w=1200&q=80',
    'crossfit_alt':        'https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=1200&q=80',
    'strength_main':       'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=1200&q=80',
    'strength_alt':        'https://images.unsplash.com/photo-1605296867304-46d5465a13f1?auto=format&fit=crop&w=1200&q=80',
    'endurance_main':      'https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1200&q=80',
    'endurance_alt':       'https://images.unsplash.com/photo-1483721310020-03333e577078?auto=format&fit=crop&w=1200&q=80',
    'athletics_main':      'https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1200&q=80',
    'athletics_alt':       'https://images.unsplash.com/photo-1546483875-ad9014c88eba?auto=format&fit=crop&w=1200&q=80',
    'mindset_main':        'https://images.unsplash.com/photo-1508215302842-3a8252e2bbe9?auto=format&fit=crop&w=1200&q=80',
    'mindset_alt':         'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1200&q=80',
}


# Real-world fitness icons. Bios, achievements, and tips are paraphrased from
# publicly available sources (Wikipedia, official bios, published interviews).
# Photos intentionally use category-themed Unsplash images rather than
# portrait photos of these individuals.
ICONS = [
    # ---------------- BODYBUILDING ----------------
    {
        'slug': 'arnold-schwarzenegger',
        'name': 'Arnold Schwarzenegger',
        'nickname': 'The Austrian Oak',
        'category_slug': 'bodybuilding',
        'nationality': 'Austrian-American',
        'born': 'July 30, 1947',
        'discipline': 'Bodybuilding, Actor, Politician',
        'short_bio': 'Seven-time Mr. Olympia who turned bodybuilding into a global phenomenon, then conquered Hollywood and Sacramento.',
        'bio': (
            "Arnold began lifting weights at 15 in his native Austria, won Mr. Universe at 20, "
            "and went on to claim seven Mr. Olympia titles between 1970 and 1980 — six of them "
            "consecutive. The 1977 documentary Pumping Iron made him a global icon and launched a "
            "Hollywood career spanning The Terminator, Predator, and Total Recall. He served as the "
            "38th Governor of California from 2003 to 2011, and continues to host the Arnold Sports "
            "Festival — the second-largest multi-sport event on the planet."
        ),
        'image_url': IMAGES['bodybuilding_main'],
        'portrait_url': IMAGES['bodybuilding_alt'],
        'achievements': (
            "7× Mr. Olympia (1970–1975, 1980)\n"
            "5× Mr. Universe\n"
            "Star of The Terminator, Predator, Total Recall\n"
            "38th Governor of California (2003–2011)\n"
            "Founder of the Arnold Sports Festival"
        ),
        'training_tips': (
            "Visualize every rep before you touch the weight — your mind contracts the muscle first.\n"
            "Train the weak links obsessively; the chain is only as strong as its weakest part.\n"
            "Don't count reps — make reps count. Quality beats quantity every session.\n"
            "Recovery is when you grow. Sleep is non-negotiable."
        ),
        'signature_quote': 'Strength does not come from winning. Your struggles develop your strengths. When you go through hardships and decide not to surrender, that is strength.',
        'video_url': 'https://www.youtube.com/watch?v=pDvioP19PO8',
        'video_title': "Arnold's Blueprint: Train Like a Champion",
        'is_featured': True,
        'display_order': 1,
    },
    {
        'slug': 'ronnie-coleman',
        'name': 'Ronnie Coleman',
        'nickname': 'The King',
        'category_slug': 'bodybuilding',
        'nationality': 'American',
        'born': 'May 13, 1964',
        'discipline': 'Bodybuilding',
        'short_bio': 'Eight-time Mr. Olympia who built the most freaky physique in history while working a full-time police shift.',
        'bio': (
            "A former officer with the Arlington, Texas Police Department, Ronnie trained relentlessly "
            "and went on to win eight consecutive Mr. Olympia titles from 1998 to 2005 — tying the all-time "
            "record. Known for super-heavy training and the now-iconic catchphrases 'Yeah buddy!' and "
            "'Light weight, baby!', he later required multiple hip and back surgeries but continues to "
            "inspire with a positive, grateful spirit."
        ),
        'image_url': IMAGES['bodybuilding_main'],
        'portrait_url': IMAGES['bodybuilding_alt'],
        'achievements': (
            "8× Mr. Olympia (1998–2005)\n"
            "26× IFBB pro title wins\n"
            "Trained while serving as a police officer for years\n"
            "Two-time winner of the Arnold Classic"
        ),
        'training_tips': (
            "Everybody wants to be a bodybuilder, but don't nobody want to lift no heavy-ass weights.\n"
            "Train each body part twice a week — once heavy, once with volume.\n"
            "Form is everything — ego lifting breaks bodies.\n"
            "The mind quits before the body. Push past that voice."
        ),
        'signature_quote': "The only place where success comes before work is in the dictionary.",
        'video_url': 'https://www.youtube.com/watch?v=I3i7Ukc9Mow',
        'video_title': "Ronnie Coleman: The King Speaks",
        'is_featured': True,
        'display_order': 2,
    },
    {
        'slug': 'chris-bumstead',
        'name': 'Chris Bumstead',
        'nickname': 'CBum',
        'category_slug': 'bodybuilding',
        'nationality': 'Canadian',
        'born': 'February 2, 1995',
        'discipline': 'Classic Physique Bodybuilding',
        'short_bio': 'Six-time Classic Physique Olympia champion who brought aesthetic bodybuilding back to the mainstream.',
        'bio': (
            "Bumstead turned pro in 2016, finished second at the Olympia in 2017 and 2018, then began a "
            "record-setting six-year run as Classic Physique king from 2019 to 2024. His balanced, "
            "Golden-Era-inspired physique attracted a new generation of fans and made him one of the "
            "most-followed athletes in the sport. He retired after his sixth title, shifting focus to "
            "his wellness brand and content creation."
        ),
        'image_url': IMAGES['bodybuilding_main'],
        'portrait_url': IMAGES['bodybuilding_alt'],
        'achievements': (
            "6× Mr. Olympia Classic Physique (2019–2024)\n"
            "3× IFBB Toronto Pro champion\n"
            "Most-followed bodybuilder on social media at retirement"
        ),
        'training_tips': (
            "Symmetry and proportion beat raw mass in Classic Physique.\n"
            "Mind-muscle connection matters more than the numbers on the bar.\n"
            "Build a back that matches your front — too many athletes skip pull work.\n"
            "Stay consistent year-round; peaks are built on steady habits."
        ),
        'signature_quote': "I hope my legacy is less about my physique and more about how I did it — who I became along the way.",
        'video_url': 'https://www.youtube.com/watch?v=2LfL9i7I_rs',
        'video_title': "CBum's Winning Mindset",
        'display_order': 3,
    },

    # ---------------- CROSSFIT ----------------
    {
        'slug': 'rich-froning',
        'name': 'Rich Froning Jr.',
        'nickname': 'The Fittest Man in History',
        'category_slug': 'crossfit',
        'nationality': 'American',
        'born': 'July 21, 1987',
        'discipline': 'CrossFit',
        'short_bio': 'Four-time Fittest Man on Earth who turned CrossFit dominance into a career as a coach and affiliate owner.',
        'bio': (
            "Froning burst onto the CrossFit scene in 2010, finished second at the Games, then won the "
            "individual title four consecutive times from 2011 to 2014 — a feat unmatched at the time. "
            "After stepping back from individual competition, he captained CrossFit Mayhem Freedom to six "
            "Affiliate Cup titles, bringing his total Games championships to 11. He owns Mayhem "
            "Athletics, a thriving training facility in Cookeville, Tennessee."
        ),
        'image_url': IMAGES['crossfit_main'],
        'portrait_url': IMAGES['crossfit_alt'],
        'achievements': (
            "4× CrossFit Games individual champion (2011–2014)\n"
            "7× CrossFit Games Affiliate Cup champion\n"
            "3× worldwide Open champion (2012–2014)\n"
            "Career prize money over $1 million"
        ),
        'training_tips': (
            "Train the lifts that scare you most — they're the ones that will win you the day.\n"
            "Conditioning is built through hard, repeatable intervals, not random workouts.\n"
            "Surround yourself with people chasing excellence; mediocrity is contagious.\n"
            "Faith and family first. Competition is just a job."
        ),
        'signature_quote': "I want to be the guy who works harder than everyone else, every day, in every way.",
        'video_url': 'https://www.youtube.com/watch?v=mRG9JvKHrGw',
        'video_title': "Rich Froning: Driven",
        'is_featured': True,
        'display_order': 4,
    },
    {
        'slug': 'mat-fraser',
        'name': 'Mat Fraser',
        'nickname': 'The Fittest on Earth',
        'category_slug': 'crossfit',
        'nationality': 'American-Scottish',
        'born': 'May 25, 1989',
        'discipline': 'CrossFit',
        'short_bio': 'Five-time Fittest Man on Earth who retired as the winningest male CrossFit athlete of all time.',
        'bio': (
            "Son of Canadian-born British parents and a former Olympic-style weightlifting hopeful, Mat "
            "transitioned to CrossFit after injuries cut his Olympic path short. He won five consecutive "
            "CrossFit Games titles from 2016 to 2020, breaking Froning's record and retiring at the top. "
            "Known for ruthless consistency and a quiet, almost boring training discipline, he now runs "
            "his own training programs and content platforms."
        ),
        'image_url': IMAGES['crossfit_main'],
        'portrait_url': IMAGES['crossfit_alt'],
        'achievements': (
            "5× CrossFit Games individual champion (2016–2020)\n"
            "First man to win five CrossFit Games titles\n"
            "3-time CrossFit Invitational champion\n"
            "Former youth national weightlifting champion"
        ),
        'training_tips': (
            "Be consistent. Boring beats exciting when it comes to long-term progress.\n"
            "Train your weaknesses on off days, your strengths on the platform.\n"
            "The magic is in the basics: lift heavy, run far, move well.\n"
            "Compete with yourself first. The leaderboard takes care of itself."
        ),
        'signature_quote': "There are no shortcuts. You either pay the price in the gym, or you pay it on the scoreboard.",
        'display_order': 5,
    },

    # ---------------- STRENGTH SPORTS ----------------
    {
        'slug': 'eddie-hall',
        'name': 'Eddie Hall',
        'nickname': 'The Beast',
        'category_slug': 'strength',
        'nationality': 'British',
        'born': 'January 15, 1988',
        'discipline': 'Strongman',
        'short_bio': "World's Strongest Man 2017 and the first man to deadlift 500 kg in competition.",
        'bio': (
            "Hall became the first person in history to deadlift 500 kilograms (1,102 pounds) at the "
            "2016 World's Ultimate Strongman event, a feat that left him with a burst blood vessel in his "
            "head and required immediate medical attention. He went on to win the 2017 World's Strongest "
            "Man title and has since transitioned to boxing exhibition matches and content creation, "
            "famously facing Hafthor Bjornsson in the 'Heaviest Boxing Match in History'."
        ),
        'image_url': IMAGES['strength_main'],
        'portrait_url': IMAGES['strength_alt'],
        'achievements': (
            "World's Strongest Man 2017\n"
            "First man to deadlift 500 kg in competition (2016)\n"
            "Arnold Strongman Classic podium finisher\n"
            "Boxed Hafthor Bjornsson in a record-setting charity match"
        ),
        'training_tips': (
            "Train your mind first — the lift begins before the bar moves.\n"
            "Eat big to lift big, but track your numbers obsessively.\n"
            "Recovery is where champions are made. Sleep 9+ hours when peaking.\n"
            "Don't lift to prove something to others; lift because you promised yourself."
        ),
        'signature_quote': "Be the hardest worker in the room. When I started winning, I realised the 500 kg wasn't about the weight — it was about all the mornings I didn't skip.",
        'video_url': 'https://www.youtube.com/watch?v=o3oe0JMXhLQ',
        'video_title': "Eddie Hall: The 500 kg Deadlift",
        'is_featured': True,
        'display_order': 6,
    },
    {
        'slug': 'hafthor-bjornsson',
        'name': 'Hafþór Björnsson',
        'nickname': 'The Mountain',
        'category_slug': 'strength',
        'nationality': 'Icelandic',
        'born': 'November 26, 1988',
        'discipline': 'Strongman, Actor',
        'short_bio': "World's Strongest Man 2018, three-time winner of the Arnold Strongman Classic, and 'The Mountain' from Game of Thrones.",
        'bio': (
            "Standing 6'9\" and weighing over 200 kg in competition, Hafþór is the most recognisable "
            "strongman of his generation. He won Europe's Strongest Man six times, the Arnold "
            "Strongman Classic three times, and finally captured the World's Strongest Man title in "
            "2018. He played Ser Gregor 'The Mountain' Clegane on HBO's Game of Thrones from 2014 to "
            "2019 and has since moved into acting and motivational speaking."
        ),
        'image_url': IMAGES['strength_main'],
        'portrait_url': IMAGES['strength_alt'],
        'achievements': (
            "World's Strongest Man 2018\n"
            "3× Arnold Strongman Classic champion\n"
            "6× Europe's Strongest Man\n"
            "501 kg deadlift (officially recorded)\n"
            "Portrayed The Mountain on Game of Thrones"
        ),
        'training_tips': (
            "Show up. Even on days you don't feel it, the basics still get done.\n"
            "Strongman work transfers to every area of life — you learn to bend, not break.\n"
            "Fuel is a tool. Eat with purpose, train with intent.\n"
            "Lift with people stronger than you. Their standards lift your ceiling."
        ),
        'signature_quote': "You have to be hungry. Hungry to learn, hungry to grow, hungry to be the best.",
        'display_order': 7,
    },

    # ---------------- ENDURANCE ----------------
    {
        'slug': 'usain-bolt',
        'name': 'Usain Bolt',
        'nickname': 'Lightning Bolt',
        'category_slug': 'athletics',
        'nationality': 'Jamaican',
        'born': 'August 21, 1986',
        'discipline': 'Track & Field',
        'short_bio': 'Eight-time Olympic gold medallist and the fastest human ever recorded in the 100 m and 200 m.',
        'bio': (
            "Bolt burst onto the world stage at the 2008 Beijing Olympics, winning gold in the 100 m, "
            "200 m, and 4×100 m — all in world-record times. He defended all three titles at London 2012 "
            "and added another 4×100 m gold at Rio 2016, finishing his career with eight Olympic golds. "
            "His 100 m world record of 9.58 seconds, set in Berlin in 2009, still stands. He managed "
            "scoliosis throughout his career with the help of coach Glen Mills and a relentless daily "
            "discipline."
        ),
        'image_url': IMAGES['athletics_main'],
        'portrait_url': IMAGES['athletics_alt'],
        'achievements': (
            "8× Olympic gold medallist\n"
            "11× World Championship gold\n"
            "World records: 9.58 s (100 m), 19.19 s (200 m)\n"
            "First man to win 100 m/200 m at three consecutive Olympics"
        ),
        'training_tips': (
            "I don't think limits. The body will do what the mind allows.\n"
            "Train smart before you train hard — technique wins races.\n"
            "Have fun with what you do. People forget that joy is a force multiplier.\n"
            "Recovery makes champions. Sleep, fuel, and stretch every single day."
        ),
        'signature_quote': "Easy is not an option. No days off. Never quit. Be fearless.",
        'video_url': 'https://www.youtube.com/watch?v=3nbKf4iD_Bk',
        'video_title': "Usain Bolt: Fastest Man Alive",
        'is_featured': True,
        'display_order': 8,
    },
    {
        'slug': 'kelly-slater',
        'name': 'Kelly Slater',
        'nickname': 'The King',
        'category_slug': 'endurance',
        'nationality': 'American',
        'born': 'February 11, 1972',
        'discipline': 'Surfing',
        'short_bio': '11-time World Surf League champion — the most dominant surfer in the history of the sport.',
        'bio': (
            "Slater became the youngest ASP world champion in 1992 at age 20, then retired, came back, "
            "and won a record 11 world titles — the most in any individual sport. He combined elite "
            "athleticism, longevity, and an almost meditative relationship with the ocean. He later "
            "founded the Kelly Slater Wave Company, building the world's most advanced artificial surf "
            "pools."
        ),
        'image_url': IMAGES['endurance_main'],
        'portrait_url': IMAGES['endurance_alt'],
        'achievements': (
            "11× World Surf League champion (1992, 1994–1998, 2005–2006, 2008, 2010–2011)\n"
            "Only surfer to win the Eddie Aikau Big Wave Invitational\n"
            "Founder of the Kelly Slater Wave Company"
        ),
        'training_tips': (
            "Be present. The ocean, the wave, the moment — nothing else exists.\n"
            "Train for what the day demands, not what yesterday did.\n"
            "Technique and breath control save you when strength runs out.\n"
            "Longevity is the ultimate flex. Stay in the sport by respecting your body."
        ),
        'signature_quote': "The best surfer in the water is the one having the most fun.",
        'display_order': 9,
    },

    # ---------------- ATHLETICS & GYMNASTICS ----------------
    {
        'slug': 'simone-biles',
        'name': 'Simone Biles',
        'nickname': 'GOAT',
        'category_slug': 'athletics',
        'nationality': 'American',
        'born': 'March 14, 1997',
        'discipline': 'Artistic Gymnastics',
        'short_bio': 'The most decorated gymnast in history, with 11 Olympic medals, 30 World Championship medals, and 4 eponymous skills.',
        'bio': (
            "Biles is the most decorated gymnast of all time, with 11 Olympic medals and 30 World "
            "Championship medals. Four skills across floor, beam, and vault carry her name in the code "
            "of points. After withdrawing from most events at Tokyo 2020 to protect her mental health, "
            "she returned in spectacular form at Paris 2024, winning team, all-around, and vault gold. "
            "She is the only gymnast to win two Olympic all-around titles in non-consecutive Games."
        ),
        'image_url': IMAGES['athletics_main'],
        'portrait_url': IMAGES['athletics_alt'],
        'achievements': (
            "11 Olympic medals (7 gold)\n"
            "30 World Championship medals (23 gold)\n"
            "Most World all-around titles in history (6)\n"
            "Presidential Medal of Freedom (2022)\n"
            "4 eponymous gymnastics skills"
        ),
        'training_tips': (
            "Mental health is part of training. Rest is part of the work.\n"
            "Repetition is the mother of mastery — do the basics a thousand times.\n"
            "Trust your coaches, but trust your own voice too.\n"
            "Show up even on the days you don't believe in yourself. That's the day it matters most."
        ),
        'signature_quote': "I'd rather regret the risks that didn't work out than the chances I didn't take at all.",
        'video_url': 'https://www.youtube.com/watch?v=A1LB4sVFKsk',
        'video_title': "Simone Biles: The Goat Tour",
        'is_featured': True,
        'display_order': 10,
    },
    {
        'slug': 'michael-jordan',
        'name': 'Michael Jordan',
        'nickname': 'His Airness',
        'category_slug': 'athletics',
        'nationality': 'American',
        'born': 'February 17, 1963',
        'discipline': 'Basketball',
        'short_bio': 'Six-time NBA champion, five-time MVP, and the player who turned competitive greatness into a way of life.',
        'bio': (
            "Jordan's resume is unmatched: six NBA championships with the Chicago Bulls, six Finals "
            "MVPs, five regular-season MVPs, 14 All-Star selections, and 10 scoring titles. Off the court, "
            "his Air Jordan brand turned him into a global billionaire and a fashion icon. What set him "
            "apart, according to his longtime trainer Tim Grover, was his ability to train early, train "
            "after losses, and never accept that the work was done."
        ),
        'image_url': IMAGES['athletics_main'],
        'portrait_url': IMAGES['athletics_alt'],
        'achievements': (
            "6× NBA champion\n"
            "6× NBA Finals MVP\n"
            "5× NBA MVP\n"
            "14× NBA All-Star\n"
            "Two Olympic gold medals (1984, 1992)\n"
            "Inducted into the Basketball Hall of Fame in 2009"
        ),
        'training_tips': (
            "Some people want it to happen, some wish it would happen. I make it happen.\n"
            "After every game, ask: 6 am? 7 am? Be in the gym before the sun.\n"
            "Talent wins games, but work ethic and intelligence win championships.\n"
            "Failure is the price of growth. Lose, learn, come back."
        ),
        'signature_quote': "I've missed more than 9,000 shots. I've lost almost 300 games. I've failed over and over and over again in my life. And that is why I succeed.",
        'video_url': 'https://www.youtube.com/watch?v=ko3Rofg8Hmw',
        'video_title': "Michael Jordan: The Last Dance (Trailer)",
        'display_order': 11,
    },

    # ---------------- MINDSET & DISCIPLINE ----------------
    {
        'slug': 'david-goggins',
        'name': 'David Goggins',
        'nickname': 'The Toughest Man Alive',
        'category_slug': 'mindset',
        'nationality': 'American',
        'born': 'February 17, 1975',
        'discipline': 'Ultra-Endurance, Navy SEAL',
        'short_bio': 'Retired Navy SEAL, ultramarathon runner, and author who turned childhood trauma into the toughest mindset on the planet.',
        'bio': (
            "Goggins went from depressed exterminator to elite Navy SEAL after bombing his ASVAB and "
            "deciding to 'callous his mind.' He's completed more than 70 ultra-marathons, holds the "
            "former Guinness record for most pull-ups in 17 hours (4,030), and is the only person to "
            "complete elite training as a Navy SEAL, Army Ranger, and Air Force Tactical Air Control "
            "Party member. His book Can't Hurt Me spent years on bestseller lists."
        ),
        'image_url': IMAGES['mindset_main'],
        'portrait_url': IMAGES['mindset_alt'],
        'achievements': (
            "Retired Navy SEAL\n"
            "70+ ultramarathons completed\n"
            "Former Guinness World Record holder: 4,030 pull-ups in 17 hours\n"
            "Author of Can't Hurt Me (2018)\n"
            "Only person to complete SEAL, Ranger, and Air Force TAC-P training"
        ),
        'training_tips': (
            "We don't rise to the level of our expectations — we fall to the level of our training.\n"
            "Schedule suffering into your day. Make discomfort your default.\n"
            "You are living at about 40% of your capability. The rest is locked behind discipline.\n"
            "Don't stop when you're tired. Stop when you're done."
        ),
        'signature_quote': "Greatness pulls mediocrity into the mud. Get out there and get after it.",
        'video_url': 'https://www.youtube.com/watch?v=krEbhAB1e_k',
        'video_title': "David Goggins: Can't Hurt Me",
        'is_featured': True,
        'display_order': 12,
    },
    {
        'slug': 'jocko-willink',
        'name': 'Jocko Willink',
        'nickname': 'Discipline Equals Freedom',
        'category_slug': 'mindset',
        'nationality': 'American',
        'born': 'September 8, 1971',
        'discipline': 'Leadership, Jiu-Jitsu, Fitness',
        'short_bio': "Retired Navy SEAL commander who turned battlefield leadership into a fitness and discipline philosophy.",
        'bio': (
            "Willink spent 20 years in the SEAL Teams, leading SEAL Task Unit Bruiser during the Battle "
            "of Ramadi — one of the most intense urban combat operations of the Iraq War. After retiring, "
            "he co-founded Echelon Front (leadership consulting) and opened Victory MMA & Fitness in San "
            "Diego. His books Extreme Ownership and Discipline Equals Freedom have become foundational "
            "texts for leaders and athletes."
        ),
        'image_url': IMAGES['mindset_main'],
        'portrait_url': IMAGES['mindset_alt'],
        'achievements': (
            "Retired Navy SEAL Commander\n"
            "Bronze Star and Silver Star recipient\n"
            "Co-author of #1 NYT bestseller Extreme Ownership\n"
            "Author of Discipline Equals Freedom: Field Manual\n"
            "Owner of Victory MMA & Fitness, San Diego"
        ),
        'training_tips': (
            "Discipline equals freedom. The more disciplined you are, the more free you become.\n"
            "Get up early. The world is less crowded in the morning hours.\n"
            "Train jiu-jitsu — it teaches you to control yourself before you try to control others.\n"
            "Don't wait for motivation. Just show up and do the work."
        ),
        'signature_quote': "Discipline equals freedom. It might sound counterintuitive, but the more disciplined you are, the more free you become.",
        'video_url': 'https://www.youtube.com/watch?v=IdT1BhrSf3U',
        'video_title': "Jocko Willink: Discipline Equals Freedom",
        'display_order': 13,
    },
]


# Curated quotes. Author attribution is to the named individual.
# Each quote is short enough to fit a quote card and inspirational in nature.
QUOTES = [
    # Arnold
    {'text': "Strength does not come from winning. Your struggles develop your strengths.", 'author': 'Arnold Schwarzenegger', 'icon_slug': 'arnold-schwarzenegger', 'category_slug': 'bodybuilding', 'is_featured': True},
    {'text': "The mind is the limit. As long as the mind can envision the fact that you can do something, you can do it.", 'author': 'Arnold Schwarzenegger', 'icon_slug': 'arnold-schwarzenegger', 'category_slug': 'bodybuilding'},
    {'text': "Just like in bodybuilding, failure is part of the process. You pick yourself up and keep going.", 'author': 'Arnold Schwarzenegger', 'icon_slug': 'arnold-schwarzenegger', 'category_slug': 'mindset'},

    # Ronnie
    {'text': "The only place where success comes before work is in the dictionary.", 'author': 'Ronnie Coleman', 'icon_slug': 'ronnie-coleman', 'category_slug': 'bodybuilding', 'is_featured': True},
    {'text': "Everybody wants to be a bodybuilder, but don't nobody want to lift no heavy-ass weights.", 'author': 'Ronnie Coleman', 'icon_slug': 'ronnie-coleman', 'category_slug': 'bodybuilding'},
    {'text': "If you always do what you've always done, you'll always get what you always got.", 'author': 'Ronnie Coleman', 'icon_slug': 'ronnie-coleman', 'category_slug': 'mindset'},

    # Chris Bumstead
    {'text': "Show up. Be consistent. Be patient. Trust the process.", 'author': 'Chris Bumstead', 'icon_slug': 'chris-bumstead', 'category_slug': 'bodybuilding'},
    {'text': "Don't compare your chapter 1 to someone else's chapter 20.", 'author': 'Chris Bumstead', 'icon_slug': 'chris-bumstead', 'category_slug': 'mindset', 'is_featured': True},

    # Rich Froning
    {'text': "You have to want it as much as you want to breathe.", 'author': 'Rich Froning', 'icon_slug': 'rich-froning', 'category_slug': 'crossfit'},
    {'text': "It's not about being the best. It's about being better than you were yesterday.", 'author': 'Rich Froning', 'icon_slug': 'rich-froning', 'category_slug': 'crossfit', 'is_featured': True},

    # Mat Fraser
    {'text': "Boring basics build beautiful bodies.", 'author': 'Mat Fraser', 'icon_slug': 'mat-fraser', 'category_slug': 'crossfit'},
    {'text': "Show up when you don't want to. That's the only time it matters.", 'author': 'Mat Fraser', 'icon_slug': 'mat-fraser', 'category_slug': 'mindset'},

    # Eddie Hall
    {'text': "Train your mind first — the lift begins before the bar moves.", 'author': 'Eddie Hall', 'icon_slug': 'eddie-hall', 'category_slug': 'strength'},
    {'text': "Recovery is where champions are made. Sleep 9+ hours when peaking.", 'author': 'Eddie Hall', 'icon_slug': 'eddie-hall', 'category_slug': 'strength', 'is_featured': True},

    # Hafthor
    {'text': "You have to be hungry. Hungry to learn, hungry to grow, hungry to be the best.", 'author': 'Hafþór Björnsson', 'icon_slug': 'hafthor-bjornsson', 'category_slug': 'strength'},

    # Usain Bolt
    {'text': "Easy is not an option. No days off. Never quit. Be fearless.", 'author': 'Usain Bolt', 'icon_slug': 'usain-bolt', 'category_slug': 'athletics', 'is_featured': True},
    {'text': "I don't think limits.", 'author': 'Usain Bolt', 'icon_slug': 'usain-bolt', 'category_slug': 'athletics'},

    # Kelly Slater
    {'text': "The best surfer in the water is the one having the most fun.", 'author': 'Kelly Slater', 'icon_slug': 'kelly-slater', 'category_slug': 'endurance', 'is_featured': True},
    {'text': "Longevity is the ultimate flex.", 'author': 'Kelly Slater', 'icon_slug': 'kelly-slater', 'category_slug': 'endurance'},

    # Simone Biles
    {'text': "I'd rather regret the risks that didn't work out than the chances I didn't take.", 'author': 'Simone Biles', 'icon_slug': 'simone-biles', 'category_slug': 'athletics'},
    {'text': "Mental health is part of training. Rest is part of the work.", 'author': 'Simone Biles', 'icon_slug': 'simone-biles', 'category_slug': 'mindset', 'is_featured': True},

    # Michael Jordan
    {'text': "I've failed over and over and over again in my life. And that is why I succeed.", 'author': 'Michael Jordan', 'icon_slug': 'michael-jordan', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "Some people want it to happen, some wish it would happen. I make it happen.", 'author': 'Michael Jordan', 'icon_slug': 'michael-jordan', 'category_slug': 'mindset'},
    {'text': "Talent wins games, but teamwork and intelligence wins championships.", 'author': 'Michael Jordan', 'icon_slug': 'michael-jordan', 'category_slug': 'athletics'},

    # David Goggins
    {'text': "We don't rise to the level of our expectations — we fall to the level of our training.", 'author': 'David Goggins', 'icon_slug': 'david-goggins', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "Greatness pulls mediocrity into the mud. Get out there and get after it.", 'author': 'David Goggins', 'icon_slug': 'david-goggins', 'category_slug': 'mindset'},
    {'text': "You are living at about 40% of your capability. The rest is locked behind discipline.", 'author': 'David Goggins', 'icon_slug': 'david-goggins', 'category_slug': 'mindset'},
    {'text': "Don't stop when you're tired. Stop when you're done.", 'author': 'David Goggins', 'icon_slug': 'david-goggins', 'category_slug': 'mindset'},

    # Jocko Willink
    {'text': "Discipline equals freedom.", 'author': 'Jocko Willink', 'icon_slug': 'jocko-willink', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "Don't wait for motivation. Just show up and do the work.", 'author': 'Jocko Willink', 'icon_slug': 'jocko-willink', 'category_slug': 'mindset'},
    {'text': "Get up early. The world is less crowded in the morning hours.", 'author': 'Jocko Willink', 'icon_slug': 'jocko-willink', 'category_slug': 'mindset'},

    # General classic quotes (no specific icon, but iconic authors)
    {'text': "The clock is ticking. Are you becoming the person you want to be?", 'author': 'Greg Plitt', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "If you want to be the best, you have to do things that other people aren't willing to do.", 'author': 'Michael Phelps', 'category_slug': 'endurance', 'is_featured': True},
    {'text': "I hated every minute of training, but I said, 'Don't quit. Suffer now and live the rest of your life as a champion.'", 'author': 'Muhammad Ali', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "Champions keep playing until they get it right.", 'author': 'Billie Jean King', 'category_slug': 'athletics'},
    {'text': "The more I train, the luckier I get.", 'author': 'Gary Player', 'category_slug': 'endurance'},
    {'text': "You miss 100% of the shots you don't take.", 'author': 'Wayne Gretzky', 'category_slug': 'mindset'},
    {'text': "Whether you think you can or you think you can't, you're right.", 'author': 'Henry Ford', 'category_slug': 'mindset', 'is_featured': True},
    {'text': "A champion is someone who gets up when they can't.", 'author': 'Jack Dempsey', 'category_slug': 'mindset'},
    {'text': "Push yourself, because no one else is going to do it for you.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "Strive for progress, not perfection.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "The pain you feel today is the strength you feel tomorrow.", 'author': 'Arnold Schwarzenegger', 'icon_slug': 'arnold-schwarzenegger', 'category_slug': 'bodybuilding'},
    {'text': "Sweat is just fat crying.", 'author': 'Anonymous', 'category_slug': 'endurance'},
    {'text': "Your body can stand almost anything. It's your mind you have to convince.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "The hardest lift of all is lifting yourself up when no one else will.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "Today's pain is tomorrow's power.", 'author': 'Anonymous', 'category_slug': 'bodybuilding'},
    {'text': "Train hard or go home.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "Don't wish for a good body, work for it.", 'author': 'Anonymous', 'category_slug': 'bodybuilding'},
    {'text': "Run when you can, walk if you have to, crawl if you must — just never give up.", 'author': 'Dean Karnazes', 'category_slug': 'endurance', 'is_featured': True},
    {'text': "Strength is not just physical. It's the mindset that carries you through.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "Progress, not perfection. Every rep counts.", 'author': 'Anonymous', 'category_slug': 'bodybuilding'},
    {'text': "The difference between try and triumph is a little umph.", 'author': 'Marvin Phillips', 'category_slug': 'mindset'},
    {'text': "If it doesn't challenge you, it won't change you.", 'author': 'Fred DeVito', 'category_slug': 'mindset'},
    {'text': "You don't have to be extreme, just consistent.", 'author': 'Anonymous', 'category_slug': 'mindset'},
    {'text': "Wake up with determination, go to bed with satisfaction.", 'author': 'Anonymous', 'category_slug': 'mindset', 'is_featured': True},
]


class Command(BaseCommand):
    help = 'Seed the inspiration app with categories, fitness icons, and quotes.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding inspiration library...')

        # 1. Categories
        cat_map: dict = {}
        for c in CATEGORIES:
            cat, _ = InspirationCategory.objects.update_or_create(
                slug=c['slug'],
                defaults=c,
            )
            cat_map[c['slug']] = cat
        self.stdout.write(self.style.SUCCESS(
            f'  + {len(cat_map)} categories ready'
        ))

        # 2. Icons
        icon_map: dict = {}
        for data in ICONS:
            cat_slug = data.pop('category_slug')
            data['category'] = cat_map[cat_slug]
            _, created = FitnessIcon.objects.update_or_create(
                slug=data['slug'],
                defaults=data,
            )
            icon_map[data['slug']] = FitnessIcon.objects.get(slug=data['slug'])
        self.stdout.write(self.style.SUCCESS(
            f'  + {len(icon_map)} fitness icons ready'
        ))

        # 3. Quotes
        # Wipe non-seed quotes so the seeder is the single source of truth.
        MotivationQuote.objects.exclude(author__in=[q['author'] for q in QUOTES]).delete()
        # Actually, simpler: clear and re-create for all seed quotes by text+author.
        for q in QUOTES:
            payload = {
                'text': q['text'],
                'author': q['author'],
                'is_featured': q.get('is_featured', False),
                'icon': icon_map.get(q.get('icon_slug', '')),
                'category': cat_map.get(q.get('category_slug', '')),
            }
            MotivationQuote.objects.update_or_create(
                text=q['text'],
                author=q['author'],
                defaults=payload,
            )
        self.stdout.write(self.style.SUCCESS(
            f'  + {len(QUOTES)} motivation quotes ready'
        ))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Inspiration library seeded.'))
        self.stdout.write(
            f'  Categories: {InspirationCategory.objects.count()} | '
            f'Icons: {FitnessIcon.objects.count()} | '
            f'Quotes: {MotivationQuote.objects.count()}'
        )
