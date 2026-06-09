"""Tests for the rule-based Fitness Hub chatbot."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from chatbot import (
    coach_context,
    guidelines,
    intent,
    knowledge,
    personality,
    safety,
)
from chatbot.models import ChatSession, ChatMessage
from chatbot.responder import respond


User = get_user_model()


# ---------------------------------------------------------------------------
# Safety layer
# ---------------------------------------------------------------------------

class SafetyTests(TestCase):
    def test_empty_input_is_blocked(self):
        r = safety.check_user_input('')
        self.assertFalse(r['safe'])
        self.assertEqual(r['reason'], 'empty')

        r = safety.check_user_input('   ')
        self.assertFalse(r['safe'])
        self.assertEqual(r['reason'], 'empty')

    def test_illegal_terms_are_blocked(self):
        for term in ['steroid', 'anabolic', 'hgh']:
            r = safety.check_user_input(f'where can I buy {term}?')
            self.assertFalse(r['safe'], msg=f'{term} should be blocked')
            self.assertIn(r['reason'], ('illegal', 'substance'),
                          msg=f'{term} reason: {r["reason"]}')

    def test_harmful_content_is_blocked(self):
        r = safety.check_user_input('I want to hurt myself')
        self.assertFalse(r['safe'])
        self.assertEqual(r['reason'], 'harm')

    def test_prohibited_substances_are_blocked(self):
        for term in ['trenbolone', 'dianabol', 'ephedrine', 'clenbuterol']:
            r = safety.check_user_input(f'tell me about {term}')
            self.assertFalse(r['safe'])
            self.assertIn(r['reason'], ('illegal', 'substance'))

    def test_medical_diagnosis_is_blocked(self):
        r = safety.check_user_input('do I have diabetes?')
        self.assertFalse(r['safe'])
        self.assertEqual(r['reason'], 'medical_diagnosis')

    def test_off_topic_is_blocked(self):
        self.assertFalse(safety.is_in_scope('who is the president of france?'))
        self.assertFalse(safety.is_in_scope('tell me about bitcoin'))
        self.assertTrue(safety.is_in_scope('how do I do a push-up?'))

    def test_normal_fitness_questions_pass_safety(self):
        for q in [
            'how do I do a push-up',
            'how much protein do I need',
            'show me chest exercises',
            'recommend an exercise',
        ]:
            r = safety.check_user_input(q)
            self.assertTrue(r['safe'], msg=f'expected safe: {q}')

    def test_refusal_messages_are_distinct(self):
        reasons = ['empty', 'illegal', 'harm', 'medical_diagnosis', 'off_topic', 'substance']
        msgs = {reason: safety.safety_refusal(reason) for reason in reasons}
        # All distinct
        self.assertEqual(len(set(msgs.values())), len(reasons))

    def test_disclaimer_added_for_health_text(self):
        text = 'you should eat more protein'
        out = safety.add_disclaimer_if_health(text)
        self.assertIn(safety.MEDICAL_DISCLAIMER, out)

    def test_disclaimer_not_duplicated(self):
        text = safety.add_disclaimer_if_health('drink water')
        text2 = safety.add_disclaimer_if_health(text)
        self.assertEqual(text, text2)

    def test_sanitize_output_strips_unsafe_patterns(self):
        out = safety.sanitize_output('You definitely have diabetes.')
        self.assertNotIn('definitely have', out.lower())


# ---------------------------------------------------------------------------
# Intent classifier
# ---------------------------------------------------------------------------

class IntentTests(TestCase):
    def test_greeting(self):
        self.assertEqual(intent.classify('hello there'), intent.INTENT_GREETING)
        self.assertEqual(intent.classify('hi'), intent.INTENT_GREETING)

    def test_thanks(self):
        self.assertEqual(intent.classify('thanks!'), intent.INTENT_THANKS)

    def test_exercise_recommend(self):
        self.assertEqual(
            intent.classify('recommend an exercise for me'),
            intent.INTENT_EXERCISE_RECOMMEND,
        )

    def test_category_exercises(self):
        self.assertEqual(
            intent.classify('chest exercises please'),
            intent.INTENT_CATEGORY_EXERCISES,
        )
        self.assertEqual(
            intent.classify('show me leg workouts'),
            intent.INTENT_CATEGORY_EXERCISES,
        )

    def test_difficulty_exercises(self):
        self.assertEqual(
            intent.classify('beginner exercises'),
            intent.INTENT_DIFFICULTY_EXERCISES,
        )
        self.assertEqual(
            intent.classify('what are good advanced workouts'),
            intent.INTENT_DIFFICULTY_EXERCISES,
        )

    def test_nutrition(self):
        self.assertEqual(
            intent.classify('how much protein should I eat?'),
            intent.INTENT_NUTRITION,
        )

    def test_recovery(self):
        self.assertEqual(
            intent.classify('I am super sore, what do I do?'),
            intent.INTENT_RECOVERY,
        )

    def test_unknown_falls_back(self):
        self.assertEqual(intent.classify('blarghonk xyzzy'), intent.INTENT_FALLBACK)

    def test_empty_string_falls_back(self):
        self.assertEqual(intent.classify(''), intent.INTENT_FALLBACK)


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

class KnowledgeTests(TestCase):
    def test_app_features_have_paths(self):
        for key, feat in knowledge.APP_FEATURES.items():
            self.assertTrue(feat['path'].startswith('/'), msg=key)
            self.assertTrue(feat['summary'])

    def test_find_app_route_for_query(self):
        key, feat = knowledge.find_app_route_for_query('how do I change my password')
        self.assertIn('settings', key)
        self.assertIn('/users/settings/', feat['path'])

    def test_find_app_route_for_query_store(self):
        key, feat = knowledge.find_app_route_for_query('where is the store?')
        self.assertIn('store', key)
        self.assertEqual(feat['path'], '/store/')

    def test_find_faq_answer_protein(self):
        ans = knowledge.find_faq_answer('how much protein should I eat?')
        self.assertIsNotNone(ans)
        self.assertIn('protein', ans.lower())

    def test_find_faq_answer_returns_none_for_garbage(self):
        ans = knowledge.find_faq_answer('xqzqzx zxqzqxz xqzqxz')
        self.assertIsNone(ans)

    def test_goal_descriptions_present(self):
        for goal in ('strength', 'hypertrophy', 'endurance', 'mobility',
                     'flexibility', 'weight_loss'):
            self.assertIn(goal, knowledge.GOAL_DESCRIPTIONS)


# ---------------------------------------------------------------------------
# Responder (full conversation flow)
# ---------------------------------------------------------------------------

class ResponderTests(TestCase):
    def setUp(self):
        # Make sure at least one exercise exists for exercise-info/recommend tests
        from exercises.models import Exercise
        Exercise.objects.create(
            name='Push-up',
            slug='push-up',
            category='chest',
            difficulty='beginner',
            equipment='bodyweight',
            description='Classic bodyweight chest exercise.',
            target_muscles='Chest, triceps, front delts',
            default_sets=3,
            default_reps=10,
            form_tips='Keep your core tight and elbows at 45°.',
            common_mistakes='Letting hips sag.',
            breathing='Inhale on the way down, exhale on the push.',
            safety='Stop if you feel sharp shoulder pain.',
        )
        Exercise.objects.create(
            name='Bodyweight Squat',
            slug='bodyweight-squat',
            category='legs',
            difficulty='beginner',
            equipment='bodyweight',
            description='Foundational lower-body exercise.',
            target_muscles='Quads, glutes',
            default_sets=3,
            default_reps=15,
        )

    def test_greeting_does_not_refuse(self):
        r = respond('hello')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'greeting')

    def test_exercise_recommendation(self):
        r = respond('recommend an exercise for me')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'exercise_recommend')
        self.assertIn('Push-up', r['reply'] + ' ' + knowledge.APP_FEATURES.get('workouts', {}).get('summary', ''))

    def test_exercise_info(self):
        r = respond('how do I do a push-up?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'exercise_info')
        self.assertIn('Push-up', r['reply'])

    def test_nutrition_question_includes_disclaimer(self):
        r = respond('how much protein should I eat?')
        self.assertFalse(r['refused'])
        self.assertIn(safety.MEDICAL_DISCLAIMER, r['reply'])

    def test_illegal_request_is_refused(self):
        r = respond('how do I use anabolic steroids?')
        self.assertTrue(r['refused'])
        self.assertIn(r['reason'], ('illegal', 'substance'))

    def test_off_topic_is_refused(self):
        r = respond('who won the world cup?')
        self.assertTrue(r['refused'])
        self.assertEqual(r['reason'], 'off_topic')

    def test_empty_input_is_refused(self):
        r = respond('   ')
        self.assertTrue(r['refused'])
        self.assertEqual(r['reason'], 'empty')

    def test_recovery_includes_disclaimer(self):
        r = respond('I am super sore, what should I do?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'recovery')
        self.assertIn(safety.MEDICAL_DISCLAIMER, r['reply'])

    def test_warmup_reply(self):
        r = respond('how should I warm up?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'warmup')
        self.assertIn('Warm-up', r['reply'])

    def test_category_exercises(self):
        r = respond('show me chest exercises')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'category_exercises')
        self.assertIn('Push-up', r['reply'])

    def test_difficulty_exercises(self):
        r = respond('beginner exercises please')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'difficulty_exercises')
        self.assertIn('Push-up', r['reply'])

    def test_progress_help(self):
        r = respond('how do I track progress?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'progress_help')

    def test_settings_help_password(self):
        r = respond('how do I change my password?')
        self.assertFalse(r['refused'])
        self.assertIn('Password', r['reply'])

    def test_fallback_still_helps(self):
        r = respond('something weird and unclassifiable xyz')
        self.assertFalse(r['refused'])

    def test_motivation_intent(self):
        r = respond('motivate me')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'motivation')
        # No medical disclaimer (motivation isn't health advice)
        self.assertNotIn('not a doctor', r['reply'].lower())

    def test_motivation_lost_motivation(self):
        r = respond("I don't want to train today")
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'motivation')

    def test_motivation_lazy(self):
        r = respond("I'm feeling lazy")
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'motivation')

    def test_who_are_you_intent(self):
        r = respond('who are you?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'who_are_you')
        self.assertIn('Fitness Hub', r['reply'])

    def test_where_am_i_intent(self):
        r = respond("I'm new, where do I start?")
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'where_am_i')
        # Should mention the workout library or goals
        self.assertTrue('/exercises/' in r['reply'] or '/goals/' in r['reply'])

    def test_next_step_intent(self):
        r = respond('what should I do next?')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], 'next_step')

    def test_deep_app_help_password(self):
        r = respond('how do I change my password')
        self.assertFalse(r['refused'])
        self.assertIn('Password', r['reply'])

    def test_deep_app_help_log_workout(self):
        r = respond('how do I log a workout')
        self.assertFalse(r['refused'])
        self.assertIn('Mark Complete', r['reply'])

    def test_deep_app_help_change_goal(self):
        r = respond('how do I change my goal')
        self.assertFalse(r['refused'])
        self.assertIn('goal', r['reply'].lower())

    def test_personalized_motivation_for_logged_in_user(self):
        u = User.objects.create_user('motivateuser', 'm@example.com', 'pw12345678')
        from users.models import Profile
        Profile.objects.get_or_create(user=u)
        # No completions yet
        r = respond('motivate me', user=u)
        self.assertFalse(r['refused'])
        # Should reference the new-user state somehow
        self.assertTrue('first' in r['reply'].lower() or 'workout' in r['reply'].lower()
                        or 'pick' in r['reply'].lower() or 'streak' in r['reply'].lower())

    def test_personalized_greeting_for_logged_in_user(self):
        u = User.objects.create_user('greetuser', 'g@example.com', 'pw12345678')
        u.first_name = 'Sagar'
        u.save()
        r = respond('hello', user=u)
        self.assertFalse(r['refused'])
        self.assertIn('Sagar', r['reply'])

    def test_reply_never_claims_to_be_human(self):
        # Run several intents and check none claim to be human
        for q in [
            'hello', 'who are you', 'motivate me', 'how do I log a workout',
            'recommend an exercise', 'what should I do next',
        ]:
            r = respond(q)
            self.assertFalse(r['refused'])
            self.assertNotIn("i'm a doctor", r['reply'].lower())
            self.assertNotIn("i am a doctor", r['reply'].lower())
            self.assertNotIn("i'm a real person", r['reply'].lower())

    def test_reply_never_promises_specific_results(self):
        for q in ['how do I lose weight', 'how do I build muscle', 'recommend a plan']:
            r = respond(q)
            self.assertFalse(r['refused'])
            # No "you will lose 10kg" style promises
            self.assertNotIn('guaranteed to lose', r['reply'].lower())
            self.assertNotIn('100% effective', r['reply'].lower())


# ---------------------------------------------------------------------------
# Personality module
# ---------------------------------------------------------------------------

class PersonalityTests(TestCase):
    def test_identity_line_mentions_coach(self):
        self.assertIn('Fitness Hub', personality.identity_line())

    def test_scope_line_is_safe(self):
        line = personality.scope_line().lower()
        # Should not claim to be a doctor/dietitian/trainer
        self.assertNotIn("i'm a doctor", line)
        self.assertNotIn("i am a doctor", line)
        self.assertNotIn("i'm a real person", line)

    def test_soft_sarcasm_is_never_body_shame(self):
        # Run several times to cover random choices
        import re
        for _ in range(20):
            line = personality.soft_sarcasm(5).lower()
            self.assertNotIn('fat', line)
            self.assertFalse(re.search(r'\bloser\b', line))
            self.assertFalse(re.search(r'\bnoob\b', line))
            self.assertFalse(re.search(r'\bpathetic\b', line))

    def test_warm_encouragement_is_positive(self):
        import re
        for _ in range(20):
            line = personality.warm_encouragement(3).lower()
            # Word-boundary check (so "closer" doesn't match "loser")
            for bad in ['pathetic', 'loser', 'noob', 'terrible', 'worthless']:
                self.assertFalse(re.search(r'\b' + bad + r'\b', line),
                                 f"warm_encouragement contains {bad!r}: {line!r}")

    def test_friendly_opener_with_name(self):
        opener = personality.friendly_opener('Sagar')
        self.assertIn('Sagar', opener)

    def test_friendly_opener_without_name(self):
        opener = personality.friendly_opener('')
        # No name should mean no "  " (double-space) and no trailing name
        self.assertNotIn('  ', opener)
        self.assertNotIn('Sagar', opener)


# ---------------------------------------------------------------------------
# Guidelines (persona enforcement)
# ---------------------------------------------------------------------------

class GuidelinesTests(TestCase):
    def test_enforce_reply_strips_doctor_claim(self):
        out = guidelines.enforce_reply("I'm a doctor and you should...")
        self.assertNotIn("i'm a doctor", out.lower())

    def test_enforce_reply_strips_dietitian_claim(self):
        out = guidelines.enforce_reply("As a dietitian, I recommend...")
        # Should be rewritten/removed
        self.assertNotIn("dietitian", out.lower())

    def test_enforce_reply_softens_unsupported_promises(self):
        out = guidelines.enforce_reply("You will lose 10kg guaranteed")
        self.assertNotIn('guaranteed', out.lower())
        self.assertNotIn('you will lose 10kg', out.lower())

    def test_enforce_reply_strips_steroid_advice(self):
        out = guidelines.enforce_reply("You should take steroids to gain muscle")
        self.assertNotIn('steroids', out.lower())

    def test_enforce_reply_stops_body_shame(self):
        out = guidelines.enforce_reply("You are fat and lazy")
        # Body-shaming phrase is replaced
        self.assertNotIn('you are fat', out.lower())
        self.assertNotIn('lazy', out.lower())

    def test_enforce_reply_strips_openai_claim(self):
        out = guidelines.enforce_reply("I am a GPT-4 model from OpenAI")
        self.assertNotIn('gpt-4', out.lower())
        self.assertNotIn('openai', out.lower())

    def test_enforce_reply_handles_diagnosis(self):
        out = guidelines.enforce_reply("You definitely have diabetes")
        self.assertNotIn('definitely have', out.lower())

    def test_assert_persona_passes_clean_text(self):
        self.assertTrue(guidelines.assert_persona("You can do this. Pick an exercise."))
        self.assertTrue(guidelines.assert_persona("I'm a rule-based AI built into Fitness Hub"))

    def test_assert_persona_fails_dirty_text(self):
        self.assertFalse(guidelines.assert_persona("I'm a doctor"))
        self.assertFalse(guidelines.assert_persona("You are fat"))
        self.assertFalse(guidelines.assert_persona("You will lose 10kg guaranteed"))
        self.assertFalse(guidelines.assert_persona("Use steroids"))

    def test_hard_limits_list_is_present(self):
        # Should be a non-empty list of rules
        self.assertGreater(len(guidelines.HARD_LIMITS), 5)
        # Should mention medical disclaimer
        joined = ' '.join(guidelines.HARD_LIMITS).lower()
        self.assertIn('medical', joined)

    def test_limits_as_bullets(self):
        bullets = guidelines.limits_as_bullets()
        self.assertIn('•', bullets)
        self.assertGreater(len(bullets.split('•')), 5)


# ---------------------------------------------------------------------------
# Bot context
# ---------------------------------------------------------------------------

class CoachContextTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ctxuser', 'c@example.com', 'pw12345678')
        from users.models import Profile
        Profile.objects.get_or_create(user=self.user)

    def test_context_for_anonymous_is_empty(self):
        from django.contrib.auth.models import AnonymousUser
        ctx = coach_context.build_user_context(AnonymousUser())
        self.assertEqual(ctx, {})

    def test_context_for_new_user(self):
        ctx = coach_context.build_user_context(self.user)
        self.assertTrue(ctx['is_new'])
        self.assertEqual(ctx['streak_days'], 0)
        self.assertIsNone(ctx['days_since_last'])
        self.assertEqual(ctx['total_completions'], 0)

    def test_context_with_completions(self):
        from exercises.models import Exercise, ExerciseCompletion
        from django.utils import timezone
        import datetime
        ex = Exercise.objects.create(
            name='Test Push', slug='test-push', category='chest',
            difficulty='beginner', equipment='bodyweight',
        )
        c = ExerciseCompletion.objects.create(
            user=self.user, exercise=ex, reps=10,
        )
        # Backdate the completion by one day (auto_now_add sets it to today).
        c.date = timezone.now().date() - datetime.timedelta(days=1)
        c.save(update_fields=['date'])
        ctx = coach_context.build_user_context(self.user)
        self.assertFalse(ctx['is_new'])
        self.assertGreaterEqual(ctx['total_completions'], 1)
        self.assertEqual(ctx['days_since_last'], 1)
        self.assertGreaterEqual(ctx['streak_days'], 1)

    def test_greeting_for_context_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        greeting = coach_context.greeting_for_context({})
        self.assertIn('Fitness Hub', greeting)

        self.assertIn('Fitness Hub', greeting)

    def test_greeting_for_context_named_user(self):
        self.user.first_name = 'Sagar'
        self.user.save()
        ctx = coach_context.build_user_context(self.user)
        greeting = coach_context.greeting_for_context(ctx)
        self.assertIn('Sagar', greeting)

    def test_motivation_for_context_returns_useful_text(self):
        ctx = coach_context.build_user_context(self.user)
        msg = coach_context.motivation_for_context(ctx)
        self.assertGreater(len(msg), 30)

    def test_next_action_for_context(self):
        ctx = coach_context.build_user_context(self.user)
        msg = coach_context.next_action_for_context(ctx)
        self.assertGreater(len(msg), 20)
        # New users should be pointed at goals or exercises
        self.assertTrue('/goals/' in msg or '/exercises/' in msg)

    def test_hydrate_goal_label(self):
        ctx = {'goal': 'hypertrophy'}
        coach_context.hydrate_goal_label(ctx)
        self.assertEqual(ctx['goal_label'], 'muscle growth')

    def test_bmi_bucket_normal(self):
        bucket = coach_context._bmi_bucket(5.83, 70)  # ~70kg, 1.78m -> BMI ~22
        self.assertEqual(bucket, 'normal')

    def test_bmi_bucket_over(self):
        bucket = coach_context._bmi_bucket(5.5, 90)  # ~90kg, 1.68m -> BMI ~32
        self.assertEqual(bucket, 'obese')

    def test_bmi_bucket_no_data(self):
        self.assertIsNone(coach_context._bmi_bucket(None, None))
        self.assertIsNone(coach_context._bmi_bucket(0, 70))


# ---------------------------------------------------------------------------
# New intent classifier tests
# ---------------------------------------------------------------------------

class NewIntentTests(TestCase):
    def test_motivation_intent(self):
        self.assertEqual(intent.classify('motivate me'), intent.INTENT_MOTIVATION)
        self.assertEqual(intent.classify("I don't want to train"), intent.INTENT_MOTIVATION)
        self.assertEqual(intent.classify("I'm feeling lazy"), intent.INTENT_MOTIVATION)
        self.assertEqual(intent.classify('I am tired'), intent.INTENT_MOTIVATION)

    def test_who_are_you_intent(self):
        self.assertEqual(intent.classify('who are you?'), intent.INTENT_WHO_ARE_YOU)
        self.assertEqual(intent.classify('what are you?'), intent.INTENT_WHO_ARE_YOU)

    def test_where_am_i_intent(self):
        self.assertEqual(intent.classify("I'm new"), intent.INTENT_WHERE_AM_I)
        self.assertEqual(intent.classify('just signed up'), intent.INTENT_WHERE_AM_I)

    def test_next_step_intent(self):
        self.assertEqual(intent.classify('what should I do'), intent.INTENT_NEXT_STEP)
        self.assertEqual(intent.classify('what next'), intent.INTENT_NEXT_STEP)

    def test_deep_app_help_intent(self):
        self.assertEqual(intent.classify('how do I log a workout'),
                         intent.INTENT_DEEP_APP_HELP)
        self.assertEqual(intent.classify('how do I change my password'),
                         intent.INTENT_DEEP_APP_HELP)


# ---------------------------------------------------------------------------
# Knowledge: howto + new feature walkthroughs
# ---------------------------------------------------------------------------

class KnowledgeHowtoTests(TestCase):
    def test_find_howto_log_workout(self):
        ans = knowledge.find_howto('how do I log a workout')
        self.assertIsNotNone(ans)
        self.assertIn('Mark Complete', ans)

    def test_find_howto_change_password(self):
        ans = knowledge.find_howto('how do I change my password')
        self.assertIsNotNone(ans)
        self.assertIn('password', ans.lower())

    def test_find_howto_change_goal(self):
        ans = knowledge.find_howto('how do I change my goal')
        self.assertIsNotNone(ans)
        self.assertIn('goal', ans.lower())

    def test_find_howto_buy_something(self):
        ans = knowledge.find_howto('how do I buy something')
        self.assertIsNotNone(ans)
        self.assertIn('store', ans.lower())

    def test_find_howto_see_orders(self):
        ans = knowledge.find_howto('how do I see my orders')
        self.assertIsNotNone(ans)
        self.assertIn('orders', ans.lower())

    def test_features_have_how_field(self):
        for key, feat in knowledge.APP_FEATURES.items():
            self.assertIn('how', feat, msg=key)
            self.assertTrue(len(feat['how']) > 50, msg=key)


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

class HttpEndpointTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)

    def test_chat_page_loads_for_anonymous(self):
        r = self.client.get(reverse('chatbot:chat'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Fitness Hub Bot')

    def test_chat_api_returns_json(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn('reply', body)
        self.assertIn('intent', body)
        self.assertEqual(body['intent'], 'greeting')

    def test_chat_api_rejects_bad_json(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 400)

    def test_chat_api_logs_messages(self):
        self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'recommend an exercise'}),
            content_type='application/json',
        )
        # Anonymous session should have one user + one bot message
        from django.contrib.sessions.backends.db import SessionStore
        sess = self.client.session
        chat_sessions = ChatSession.objects.filter(session_key=sess.session_key)
        self.assertEqual(chat_sessions.count(), 1)
        msgs = chat_sessions.first().messages.all()
        self.assertEqual(msgs.count(), 2)
        self.assertEqual(msgs[0].role, 'user')
        self.assertEqual(msgs[1].role, 'bot')

    def test_chat_api_authenticated_user(self):
        User = get_user_model()
        u = User.objects.create_user('chatty', 'chatty@example.com', 'pw12345678')
        self.client.force_login(u)
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(ChatSession.objects.filter(user=u).exists())

    def test_chat_api_safety_refusal(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'tell me about anabolic steroids'}),
            content_type='application/json',
        )
        body = r.json()
        self.assertTrue(body['refused'])
        self.assertIn(body['reason'], ('illegal', 'substance'))

    def test_chat_api_suggestions_present(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        body = r.json()
        self.assertIsInstance(body['suggestions'], list)
        self.assertGreater(len(body['suggestions']), 0)

    def test_context_endpoint_for_anonymous(self):
        r = self.client.get(reverse('chatbot:context'))
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body['is_authenticated'])
        self.assertIn('greeting', body)
        self.assertIn('Fitness Hub', body['greeting'])

    def test_context_endpoint_for_logged_in_user(self):
        u = User.objects.create_user('ctxclient', 'cc@example.com', 'pw12345678')
        u.first_name = 'Sagar'
        u.save()
        from users.models import Profile
        Profile.objects.get_or_create(user=u)
        self.client.force_login(u)
        r = self.client.get(reverse('chatbot:context'))
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body['is_authenticated'])
        self.assertEqual(body['name'], 'Sagar')
        self.assertIn('Sagar', body['greeting'])

    def test_motivation_api_response(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'motivate me'}),
            content_type='application/json',
        )
        body = r.json()
        self.assertEqual(body['intent'], 'motivation')
        self.assertFalse(body['refused'])
        # Suggestions should be present
        self.assertGreater(len(body['suggestions']), 0)

    def test_who_are_you_api_response(self):
        r = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps({'message': 'who are you'}),
            content_type='application/json',
        )
        body = r.json()
        self.assertEqual(body['intent'], 'who_are_you')
        self.assertIn('Fitness Hub', body['reply'])


# ---------------------------------------------------------------------------
# Personality layer — empathetic, understanding, always body-safe
# ---------------------------------------------------------------------------

class PersonalityTests(TestCase):
    def test_soft_sarcasm_lines_are_safe(self):
        """Sarcasm must never mention body, weight, gender, or identity."""
        for _ in range(50):
            line = personality.soft_sarcasm(0)
            self.assertFalse(_is_body_attack(line), f"unsafe sarcasm: {line}")

    def test_soft_sarcasm_uses_empathetic_tone(self):
        for _ in range(50):
            line = personality.soft_sarcasm(0)
            self.assertFalse(_is_body_attack(line), f"unsafe line: {line}")
            self.assertFalse(line.startswith("Oh"), "should not start with sarcastic 'Oh'")
            self.assertFalse(line.startswith("Cool"), "should not start with sarcastic 'Cool'")
            # Should not contain guilt-tripping phrases
            self.assertFalse("'ll start Monday" in line, f"no guilt-tripping: {line}")

    def test_warm_encouragement_is_safe(self):
        for _ in range(50):
            line = personality.warm_encouragement(0)
            self.assertFalse(_is_body_attack(line), f"unsafe warm line: {line}")

    def test_friendly_opener_with_name(self):
        opener = personality.friendly_opener('Sagar')
        self.assertIn('Sagar', opener)

    def test_technique_closer_runs(self):
        closer = personality.technique_closer()
        self.assertIsInstance(closer, str)
        self.assertGreater(len(closer), 5)

    def test_sharp_question_line_runs(self):
        line = personality.sharp_question_line()
        self.assertIsInstance(line, str)
        self.assertGreater(len(line), 5)

    def test_identity_line_mentions_fitness_hub(self):
        line = personality.identity_line()
        self.assertIn('Fitness Hub', line)


def _is_body_attack(text: str) -> bool:
    """Local helper mirroring guidelines._is_body_or_identity_attack.

    Uses word-boundary matching for single-word insults so e.g. "closer"
    doesn't trigger on "loser".
    """
    import re
    bad_phrases = [
        'you are fat', "you're fat", 'your weight is', 'you look like',
        'your body is', 'you people', 'your kind', 'for a girl', 'for a boy',
        'lazy ass', 'are fat', 'are lazy',
    ]
    bad_words = ['loser', 'noob', 'pathetic']
    lowered = text.lower()
    if any(b in lowered for b in bad_phrases):
        return True
    for w in bad_words:
        if re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', lowered):
            return True
    return False


# ---------------------------------------------------------------------------
# Knowledge base — encyclopedia, principles, cardio, mobility, supplements
# ---------------------------------------------------------------------------

class KnowledgeEncyclopediaTests(TestCase):
    def test_encyclopedia_has_all_muscle_groups(self):
        expected = {'chest', 'back', 'shoulders', 'arms', 'legs', 'core', 'cardio'}
        self.assertTrue(expected.issubset(set(knowledge.EXERCISE_ENCYCLOPEDIA.keys())))

    def test_encyclopedia_lookup_chest(self):
        entry = knowledge.encyclopedia_reply('how to do chest exercises')
        self.assertIsNotNone(entry)
        self.assertIn('chest', entry.lower())

    def test_encyclopedia_lookup_legs(self):
        entry = knowledge.encyclopedia_reply('leg cues')
        self.assertIsNotNone(entry)
        self.assertIn('leg', entry.lower())

    def test_encyclopedia_lookup_unknown_returns_none(self):
        self.assertIsNone(knowledge.encyclopedia_reply('xyz not a muscle'))

    def test_encyclopedia_lists_mistakes(self):
        entry = knowledge.encyclopedia_reply('chest form')
        self.assertIn('mistakes', entry.lower())


class TrainingPrinciplesTests(TestCase):
    def test_progressive_overload_answer(self):
        a = knowledge.find_principle('how does progressive overload work')
        self.assertIsNotNone(a)
        self.assertIn('progressive overload', a.lower())

    def test_rpe_answer(self):
        a = knowledge.find_principle('what is rpe')
        self.assertIsNotNone(a)
        self.assertIn('rpe', a.lower())

    def test_deload_answer(self):
        a = knowledge.find_principle('do i need a deload')
        self.assertIsNotNone(a)
        self.assertIn('deload', a.lower())

    def test_volume_answer(self):
        a = knowledge.find_principle('how many sets per muscle')
        self.assertIsNotNone(a)
        self.assertIn('sets', a.lower())

    def test_one_rep_max_answer(self):
        a = knowledge.find_principle('what is my 1rm')
        self.assertIsNotNone(a)
        self.assertIn('1rm', a.lower())


class CardioKnowledgeTests(TestCase):
    def test_hiit_answer(self):
        a = knowledge.find_cardio_answer('what is hiit')
        self.assertIsNotNone(a)
        self.assertIn('hiit', a.lower())

    def test_liss_answer(self):
        a = knowledge.find_cardio_answer('tell me about liss')
        self.assertIsNotNone(a)
        self.assertIn('liss', a.lower())

    def test_zone_2_answer(self):
        a = knowledge.find_cardio_answer('explain zone 2')
        self.assertIsNotNone(a)
        self.assertIn('zone 2', a.lower())

    def test_beginner_running_answer(self):
        a = knowledge.find_cardio_answer('how do i start running')
        self.assertIsNotNone(a)
        self.assertIn('run', a.lower())


class MobilityKnowledgeTests(TestCase):
    def test_stretching_answer(self):
        a = knowledge.find_mobility_answer('when to stretch')
        self.assertIsNotNone(a)
        self.assertIn('stretch', a.lower())

    def test_mobility_answer(self):
        a = knowledge.find_mobility_answer('how do i improve mobility')
        self.assertIsNotNone(a)
        self.assertIn('mobility', a.lower())

    def test_cool_down_answer(self):
        a = knowledge.find_mobility_answer('best cool down routine')
        self.assertIsNotNone(a)
        self.assertIn('cool', a.lower())


class SleepRecoveryKnowledgeTests(TestCase):
    def test_sleep_answer(self):
        a = knowledge.find_sleep_recovery_answer('how much sleep do i need')
        self.assertIsNotNone(a)
        self.assertIn('sleep', a.lower())

    def test_doms_answer(self):
        a = knowledge.find_sleep_recovery_answer('what is doms')
        self.assertIsNotNone(a)
        self.assertIn('doms', a.lower())

    def test_active_recovery_answer(self):
        a = knowledge.find_sleep_recovery_answer('active recovery day')
        self.assertIsNotNone(a)
        self.assertIn('active', a.lower())


class SupplementKnowledgeTests(TestCase):
    def test_creatine_answer(self):
        a = knowledge.find_supplement_answer('is creatine safe')
        self.assertIsNotNone(a)
        self.assertIn('creatine', a.lower())

    def test_whey_answer(self):
        a = knowledge.find_supplement_answer('should i use whey protein')
        self.assertIsNotNone(a)
        self.assertIn('whey', a.lower())

    def test_caffeine_answer(self):
        a = knowledge.find_supplement_answer('caffeine pre workout')
        self.assertIsNotNone(a)
        self.assertIn('caffeine', a.lower())

    def test_overview_answer(self):
        a = knowledge.find_supplement_answer('what supplements should i take')
        self.assertIsNotNone(a)
        self.assertIn('creatine', a.lower())


class FindAnyKnowledgeTests(TestCase):
    def test_master_lookup_hits_principles(self):
        a = knowledge.find_any_knowledge('how do i progress')
        self.assertIsNotNone(a)
        self.assertIn('progress', a.lower())

    def test_master_lookup_hits_cardio(self):
        a = knowledge.find_any_knowledge('what is hiit')
        self.assertIsNotNone(a)
        self.assertIn('hiit', a.lower())

    def test_master_lookup_hits_supplements(self):
        a = knowledge.find_any_knowledge('is creatine safe')
        self.assertIsNotNone(a)
        self.assertIn('creatine', a.lower())

    def test_master_lookup_handles_empty(self):
        self.assertIsNone(knowledge.find_any_knowledge(''))


# ---------------------------------------------------------------------------
# Intent classification — new intents
# ---------------------------------------------------------------------------

class NewIntentClassificationTests(TestCase):
    def test_programming_intent(self):
        for q in ['progressive overload', 'rpe scale', 'how many sets per muscle',
                  'deload week', '1rm calculator', 'overtraining']:
            self.assertEqual(intent.classify(q), intent.INTENT_PROGRAMMING, msg=q)

    def test_cardio_intent(self):
        for q in ['what is hiit', 'tell me about liss', 'zone 2 training',
                  'how to start running', 'best cardio for fat loss']:
            self.assertEqual(intent.classify(q), intent.INTENT_CARDIO, msg=q)

    def test_mobility_intent(self):
        for q in ['tight hips', 'range of motion', 'cool down routine',
                  'mobility work', 'post workout stretch']:
            self.assertEqual(intent.classify(q), intent.INTENT_MOBILITY, msg=q)

    def test_supplements_intent(self):
        for q in ['is creatine safe', 'fish oil benefits',
                  'what supplements to take', 'vitamin d',
                  'creatine monohydrate', 'magnesium before bed']:
            self.assertEqual(intent.classify(q), intent.INTENT_SUPPLEMENTS, msg=q)

    def test_sleep_intent(self):
        for q in ['how much sleep do i need', 'sleep for muscle',
                  'active recovery', 'how to recover faster']:
            self.assertEqual(intent.classify(q), intent.INTENT_SLEEP, msg=q)


# ---------------------------------------------------------------------------
# Responder — new intents
# ---------------------------------------------------------------------------

class NewIntentResponderTests(TestCase):
    def test_programming_returns_useful_reply(self):
        r = respond('progressive overload')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], intent.INTENT_PROGRAMMING)
        self.assertGreater(len(r['reply']), 50)
        self.assertIn('overload', r['reply'].lower())

    def test_cardio_returns_useful_reply(self):
        r = respond('what is hiit')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], intent.INTENT_CARDIO)
        self.assertIn('hiit', r['reply'].lower())

    def test_mobility_returns_useful_reply(self):
        r = respond('tight hips what to do')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], intent.INTENT_MOBILITY)
        self.assertIn('hip', r['reply'].lower())

    def test_supplements_returns_useful_reply_with_disclaimer(self):
        r = respond('is creatine safe')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], intent.INTENT_SUPPLEMENTS)
        self.assertIn('creatine', r['reply'].lower())
        # Disclaimer should be present (supplements are health-related)
        self.assertIn('not a doctor', r['reply'].lower())

    def test_sleep_returns_useful_reply(self):
        r = respond('how much sleep do i need')
        self.assertFalse(r['refused'])
        self.assertEqual(r['intent'], intent.INTENT_SLEEP)
        self.assertIn('sleep', r['reply'].lower())

    def test_encyclopedia_falls_back_for_muscle_group(self):
        r = respond('chest form cues')
        self.assertFalse(r['refused'])
        # Either it routed to exercise_info (and found an exercise) or
        # it fell back to encyclopedia. Either way: useful answer.
        self.assertGreater(len(r['reply']), 50)

    def test_recovery_intent_uses_deeper_knowledge(self):
        r = respond('how much sleep do i need after a workout')
        self.assertFalse(r['refused'])
        # Should route to sleep or recovery — both have good answers.
        self.assertIn(r['intent'], (intent.INTENT_SLEEP, intent.INTENT_RECOVERY))
        self.assertGreater(len(r['reply']), 50)

