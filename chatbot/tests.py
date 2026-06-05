"""Tests for the rule-based Fitness Hub chatbot."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from chatbot import intent, knowledge, safety
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


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

class HttpEndpointTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)

    def test_chat_page_loads_for_anonymous(self):
        r = self.client.get(reverse('chatbot:chat'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Fitness Coach')

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
