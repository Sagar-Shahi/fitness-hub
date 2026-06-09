"""Tests for the gamification app: level math, XP events, badges, quests, signals, views, chatbot integration."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from gamification import models as gm
from gamification import services
from gamification.context_processors import player_summary as pp_player_summary


User = get_user_model()


def _make_user(username='tester'):
    return User.objects.create_user(username=username, password='pw12345!')


def _seed_badge(code, **kwargs):
    defaults = {
        'name': code.title(),
        'description': f'Test {code} badge',
        'icon': '🏅',
        'tier': 'bronze',
        'xp_reward': 0,
    }
    defaults.update(kwargs)
    return gm.Badge.objects.create(code=code, **defaults)


def _seed_quest(code, frequency='daily', target_type='workouts_logged', target=1, **kwargs):
    defaults = {
        'name': code.title(),
        'description': f'Test {code} quest',
        'icon': '🎯',
        'frequency': frequency,
        'target_type': target_type,
        'target_count': target,
        'xp_reward': 25,
        'coin_reward': 0,
        'weight': 10,
    }
    defaults.update(kwargs)
    return gm.Quest.objects.create(code=code, **defaults)


# ---------------------------------------------------------------------------
# Pure math
# ---------------------------------------------------------------------------

class LevelMathTests(TestCase):
    def test_xp_for_level_is_zero_at_level_1(self):
        self.assertEqual(gm.xp_for_level(1), 0)

    def test_xp_for_level_grows_quadratically(self):
        self.assertEqual(gm.xp_for_level(2), 100)
        self.assertEqual(gm.xp_for_level(3), 400)
        self.assertEqual(gm.xp_for_level(4), 900)

    def test_level_for_xp_maps_correctly(self):
        self.assertEqual(gm.level_for_xp(0), 1)
        self.assertEqual(gm.level_for_xp(99), 1)
        self.assertEqual(gm.level_for_xp(100), 2)
        self.assertEqual(gm.level_for_xp(399), 2)
        self.assertEqual(gm.level_for_xp(400), 3)
        self.assertEqual(gm.level_for_xp(900), 4)
        self.assertEqual(gm.level_for_xp(1600), 5)

    def test_title_for_level_uses_table(self):
        self.assertEqual(gm.title_for_level(1), 'Rookie')
        self.assertEqual(gm.title_for_level(5), 'Initiate')
        self.assertEqual(gm.title_for_level(20), 'Hero')
        self.assertEqual(gm.title_for_level(50), 'Immortal')
        self.assertEqual(gm.title_for_level(60), 'Transcendent')
        self.assertEqual(gm.title_for_level(99), 'Transcendent')

    def test_player_stats_properties(self):
        u = _make_user('math1')
        stats = services.get_or_create_stats(u)
        stats.xp = 150  # between L2 (100) and L3 (400)
        stats.save()
        self.assertEqual(stats.level, 2)
        self.assertEqual(stats.title, 'Rookie')  # L2 still rookie
        self.assertEqual(stats.xp_into_level, 50)
        self.assertEqual(stats.xp_to_next_level, 300)
        self.assertEqual(stats.level_progress_percent, int(50 * 100 / 300))

    def test_custom_title_overrides(self):
        u = _make_user('math2')
        stats = services.get_or_create_stats(u)
        stats.custom_title = 'Captain'
        stats.save()
        self.assertEqual(stats.title, 'Captain')


# ---------------------------------------------------------------------------
# award_xp
# ---------------------------------------------------------------------------

class AwardXPTests(TestCase):
    def setUp(self):
        self.user = _make_user('awarder')

    def test_first_award_creates_stats(self):
        self.assertFalse(gm.PlayerStats.objects.filter(user=self.user).exists())
        result = services.award_xp(self.user, 50, source='workout')
        self.assertTrue(gm.PlayerStats.objects.filter(user=self.user).exists())
        self.assertEqual(result['stats'].xp, 50)

    def test_award_writes_xp_event(self):
        services.award_xp(self.user, 25, source='workout', description='pushups')
        ev = gm.XPEvent.objects.filter(user=self.user).first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.amount, 25)
        self.assertEqual(ev.source, 'workout')
        self.assertEqual(ev.description, 'pushups')

    def test_award_zero_amount_no_op(self):
        services.award_xp(self.user, 0, source='other')
        self.assertEqual(gm.XPEvent.objects.filter(user=self.user).count(), 0)

    def test_negative_award_clamps_to_zero(self):
        services.award_xp(self.user, 50, source='workout')
        services.award_xp(self.user, -999, source='correction')
        stats = gm.PlayerStats.objects.get(user=self.user)
        self.assertEqual(stats.xp, 0)

    def test_level_up_detection(self):
        result = services.award_xp(self.user, 150, source='workout')
        self.assertEqual(result['new_level'], 2)
        self.assertTrue(result['leveled_up'])
        self.assertEqual(result['levels_gained'], 1)
        self.assertEqual(result['new_title'], 'Rookie')

    def test_multi_level_jump(self):
        # 0 -> 1000 XP should jump multiple levels
        result = services.award_xp(self.user, 1000, source='workout')
        self.assertGreaterEqual(result['levels_gained'], 2)
        self.assertTrue(result['leveled_up'])

    def test_anonymous_user_noop(self):
        result = services.award_xp(None, 100, source='workout')
        self.assertIsNone(result['stats'])
        self.assertFalse(result['leveled_up'])

    def test_updates_last_active(self):
        self.assertIsNone(gm.PlayerStats.objects.get_or_create(user=self.user)[0].last_active)
        services.award_xp(self.user, 25, source='workout')
        self.assertIsNotNone(gm.PlayerStats.objects.get(user=self.user).last_active)

    def test_grant_coins(self):
        services.grant_coins(self.user, 100)
        services.grant_coins(self.user, 50)
        stats = gm.PlayerStats.objects.get(user=self.user)
        self.assertEqual(stats.coins, 150)

    def test_grant_coins_zero_or_negative_noop(self):
        services.grant_coins(self.user, 0)
        services.grant_coins(self.user, -10)
        # grant_coins short-circuits on amount<=0, so no PlayerStats row is created.
        self.assertFalse(gm.PlayerStats.objects.filter(user=self.user).exists())


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

class BadgeTests(TestCase):
    def setUp(self):
        self.user = _make_user('badger')
        # Seed a handful of badges
        _seed_badge('first_step')
        _seed_badge('lvl_5')
        _seed_badge('lvl_20', xp_reward=200)
        _seed_badge('goal_setter')
        _seed_badge('iron_month')

    def test_unlock_via_level(self):
        services.award_xp(self.user, 5000, source='workout')  # way past Lv5
        unlocked = services.check_and_unlock_badges(self.user)
        codes = [ub.badge.code for ub in unlocked]
        # first_step requires total_workouts>=1; we only awarded XP, so it
        # should NOT be in the unlock list. lvl_5 (level>=5) should be.
        self.assertNotIn('first_step', codes)
        self.assertIn('lvl_5', codes)

    def test_unlock_via_xp_reward(self):
        # lvl_20 has xp_reward=200
        services.award_xp(self.user, 99999, source='workout')
        unlocked = services.check_and_unlock_badges(self.user)
        lvl20 = next((ub for ub in unlocked if ub.badge.code == 'lvl_20'), None)
        self.assertIsNotNone(lvl20)
        # XPEvent for the bonus should be recorded
        bonus = gm.XPEvent.objects.filter(user=self.user, source='badge', amount=200)
        self.assertTrue(bonus.exists())

    def test_already_unlocked_skipped(self):
        services.award_xp(self.user, 99999, source='workout')
        first = services.check_and_unlock_badges(self.user)
        self.assertTrue(any(ub.badge.code == 'lvl_5' for ub in first))
        second = services.check_and_unlock_badges(self.user)
        self.assertFalse(any(ub.badge.code == 'lvl_5' for ub in second))

    def test_unknown_badge_code_doesnt_crash(self):
        _seed_badge('nope_no_rule')
        # Should silently skip
        unlocked = services.check_and_unlock_badges(self.user)
        self.assertFalse(any(ub.badge.code == 'nope_no_rule' for ub in unlocked))

    def test_iron_month_unlocks_with_streak(self):
        stats, _ = gm.PlayerStats.objects.get_or_create(user=self.user)
        ws, _ = self.user.workout_stats.__class__.objects.get_or_create(user=self.user) \
            if hasattr(self.user, 'workout_stats') else (None, None)
        # Use the related WorkoutStats model directly
        from progress.models import UserWorkoutStats
        ws, _ = UserWorkoutStats.objects.get_or_create(user=self.user)
        ws.longest_streak = 30
        ws.save()
        unlocked = services.check_and_unlock_badges(self.user)
        codes = [ub.badge.code for ub in unlocked]
        self.assertIn('iron_month', codes)


# ---------------------------------------------------------------------------
# Quests
# ---------------------------------------------------------------------------

class QuestTests(TestCase):
    def setUp(self):
        self.user = _make_user('quester')
        self.q1 = _seed_quest('daily1', target=3, target_type='workouts_logged')
        self.q2 = _seed_quest('daily2', target=2, target_type='meals_logged')
        self.q3 = _seed_quest('daily3', target=4, target_type='workouts_logged')
        self.q4 = _seed_quest('weekly1', frequency='weekly', target=5, target_type='workouts_logged')

    def test_generate_daily_creates_three(self):
        uqs = services.generate_daily_quests(self.user, count=3)
        self.assertEqual(len(uqs), 3)
        self.assertTrue(all(uq.quest.frequency == 'daily' for uq in uqs))

    def test_generate_daily_idempotent_per_day(self):
        first = services.generate_daily_quests(self.user, count=3)
        second = services.generate_daily_quests(self.user, count=3)
        self.assertEqual(len(first), len(second))
        self.assertEqual(
            sorted(uq.quest_id for uq in first),
            sorted(uq.quest_id for uq in second),
        )

    def test_progress_quest_increments(self):
        services.generate_daily_quests(self.user, count=3)
        completed = services.progress_quest(self.user, 'workouts_logged', amount=5)
        # The first daily quest is a workouts_logged with target 3, so 5 should complete it.
        self.assertTrue(any(uq.status == 'completed' for uq in completed))
        uq = gm.UserQuest.objects.get(user=self.user, quest=self.q1)
        self.assertEqual(uq.progress, uq.target)  # clamped to target
        self.assertEqual(uq.status, 'completed')

    def test_claim_awards_xp_and_marks_claimed(self):
        services.generate_daily_quests(self.user, count=3)
        uq = gm.UserQuest.objects.get(user=self.user, quest=self.q1)
        uq.progress = uq.target
        uq.status = 'completed'
        uq.save()
        result = services.claim_quest(uq)
        self.assertEqual(result['xp'], self.q1.xp_reward)
        uq.refresh_from_db()
        self.assertEqual(uq.status, 'claimed')
        # Second claim is a no-op
        result2 = services.claim_quest(uq)
        self.assertTrue(result2.get('already_claimed'))

    def test_progress_does_not_affect_other_frequencies(self):
        services.generate_daily_quests(self.user, count=3)
        services.progress_quest(self.user, 'workouts_logged', amount=1)
        weekly = gm.UserQuest.objects.filter(user=self.user, quest=self.q4)
        self.assertFalse(weekly.exists())  # weekly not auto-spawned by daily generation


# ---------------------------------------------------------------------------
# Streak shields
# ---------------------------------------------------------------------------

class StreakShieldTests(TestCase):
    def setUp(self):
        self.user = _make_user('shield')

    def test_grant_and_consume(self):
        services.grant_streak_shield(self.user, 2)
        self.assertEqual(gm.PlayerStats.objects.get(user=self.user).streak_shields, 2)
        ok = services.consume_streak_shield(self.user, reason='missed day')
        self.assertTrue(ok)
        self.assertEqual(gm.PlayerStats.objects.get(user=self.user).streak_shields, 1)
        self.assertEqual(gm.StreakShieldUse.objects.filter(user=self.user).count(), 1)

    def test_consume_when_none_returns_false(self):
        self.assertFalse(services.consume_streak_shield(self.user))
        self.assertEqual(gm.StreakShieldUse.objects.count(), 0)

    def test_grant_zero_or_negative_noop(self):
        services.grant_streak_shield(self.user, 0)
        services.grant_streak_shield(self.user, -5)
        # grant_streak_shield short-circuits on count<=0, so no PlayerStats row is created.
        self.assertFalse(gm.PlayerStats.objects.filter(user=self.user).exists())


# ---------------------------------------------------------------------------
# Context processor
# ---------------------------------------------------------------------------

class ContextProcessorTests(TestCase):
    def test_returns_empty_summary_for_anonymous(self):
        class FakeReq:
            user = None
        out = pp_player_summary(FakeReq())
        # Context processor wraps in a single key
        self.assertIn('player_summary', out)
        self.assertEqual(out['player_summary'], {})

    def test_returns_summary_for_authenticated(self):
        u = _make_user('ctx')
        services.award_xp(u, 50)
        out = pp_player_summary(type('R', (), {'user': u})())
        self.assertIn('player_summary', out)
        summary = out['player_summary']
        self.assertIn('level', summary)
        self.assertEqual(summary['xp'], 50)
        self.assertEqual(summary['level'], 1)


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

class SignalTests(TestCase):
    """Make sure signal handlers run and award XP, but never break the underlying save."""
    def setUp(self):
        self.user = _make_user('signaler')

    def test_goal_save_awards_xp(self):
        from goals.models import Goal
        with patch.object(services, 'award_xp') as mock:
            Goal.objects.create(
                user=self.user,
                goal_type='muscle_gain',
                target_weight=75,
            )
        self.assertTrue(mock.called)
        # Source can be passed as positional or kwarg
        args, kwargs = mock.call_args
        self.assertEqual(kwargs.get('source', args[1] if len(args) > 1 else None), 'goal')

    def test_signal_failure_does_not_break_save(self):
        from goals.models import Goal
        with patch.object(services, 'award_xp', side_effect=Exception('boom')):
            goal = Goal.objects.create(
                user=self.user,
                goal_type='fat_loss',
                target_weight=70,
            )
        self.assertIsNotNone(goal.pk)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = _make_user('viewer')
        self.client.force_login(self.user)

    def test_index_loads(self):
        r = self.client.get(reverse('gamification:index'))
        self.assertEqual(r.status_code, 200)

    def test_index_consumes_session_announcements(self):
        # Seed an announcement, hit index, confirm it's cleared.
        session = self.client.session
        session['gamification_levelup'] = '{"level": 3, "title": "Apprentice", "levels_gained": 1}'
        session.save()
        r = self.client.get(reverse('gamification:index'))
        self.assertEqual(r.status_code, 200)
        # Session key should be gone after the response.
        self.assertNotIn('gamification_levelup', self.client.session)

    def test_badges_loads(self):
        r = self.client.get(reverse('gamification:badges'))
        self.assertEqual(r.status_code, 200)

    def test_quests_loads(self):
        r = self.client.get(reverse('gamification:quests'))
        self.assertEqual(r.status_code, 200)

    def test_leaderboard_loads(self):
        r = self.client.get(reverse('gamification:leaderboard'))
        self.assertEqual(r.status_code, 200)

    def test_anon_redirected_from_index(self):
        self.client.logout()
        r = self.client.get(reverse('gamification:index'))
        self.assertEqual(r.status_code, 302)

    def test_refresh_quests_works(self):
        # Seed at least one daily quest template first; otherwise nothing can spawn.
        _seed_quest('seeded_for_refresh', frequency='daily', target=2, target_type='workouts_logged')
        r = self.client.post(reverse('gamification:refresh-quests'))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(gm.UserQuest.objects.filter(user=self.user).exists())

    def test_claim_quest_happy_path(self):
        q = _seed_quest('claimtest', target=1, target_type='workouts_logged', xp_reward=50)
        uq = gm.UserQuest.objects.create(
            user=self.user, quest=q, target=1, progress=1, status='completed',
        )
        r = self.client.post(reverse('gamification:claim-quest', args=[uq.id]))
        self.assertEqual(r.status_code, 302)
        uq.refresh_from_db()
        self.assertEqual(uq.status, 'claimed')
        self.assertEqual(gm.PlayerStats.objects.get(user=self.user).xp, 50)

    def test_claim_quest_redirects_to_index(self):
        q = _seed_quest('redirtest', target=1, xp_reward=10)
        uq = gm.UserQuest.objects.create(
            user=self.user, quest=q, target=1, progress=1, status='completed',
        )
        r = self.client.post(reverse('gamification:claim-quest', args=[uq.id]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse('gamification:index'))

    def test_claim_quest_other_user_404(self):
        other = _make_user('other')
        q = _seed_quest('cross', target=1)
        uq = gm.UserQuest.objects.create(user=other, quest=q, progress=1, status='completed')
        r = self.client.post(reverse('gamification:claim-quest', args=[uq.id]))
        self.assertEqual(r.status_code, 404)
        uq.refresh_from_db()
        self.assertEqual(uq.status, 'completed')

    def test_api_summary_requires_auth(self):
        self.client.logout()
        r = self.client.get(reverse('gamification:api-summary'))
        # @login_required redirects to /accounts/login/?next=...
        self.assertIn(r.status_code, (302, 401, 403))

    def test_api_summary_authenticated(self):
        r = self.client.get(reverse('gamification:api-summary'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('level', r.json())


# ---------------------------------------------------------------------------
# Chatbot integration
# ---------------------------------------------------------------------------

class ChatbotPlayIntentTests(TestCase):
    def setUp(self):
        self.user = _make_user('chatter')

    def test_my_level_intent(self):
        from chatbot.responder import respond
        r = respond('what level am i', user=self.user)
        self.assertIn('Level', r['reply'])
        self.assertEqual(r['intent'], 'play_status')

    def test_my_badges_intent(self):
        from chatbot.responder import respond
        r = respond('show my badges', user=self.user)
        self.assertEqual(r['intent'], 'play_help')
        # Reply should mention the play system
        self.assertIn('play', r['reply'].lower())

    def test_anon_user_level_intent_doesnt_crash(self):
        from chatbot.responder import respond
        r = respond('my level', user=None)
        self.assertFalse(r.get('refused'))
        self.assertIn('signed in', r['reply'].lower())


# ---------------------------------------------------------------------------
# Admin smoke
# ---------------------------------------------------------------------------

class AdminSmokeTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser('admin', 'a@a.com', 'pw')
        self.client.force_login(admin)

    def test_admin_pages_load(self):
        for url_name in [
            'admin:gamification_playerstats_changelist',
            'admin:gamification_badge_changelist',
            'admin:gamification_quest_changelist',
            'admin:gamification_userbadge_changelist',
            'admin:gamification_userquest_changelist',
            'admin:gamification_xpevent_changelist',
        ]:
            r = self.client.get(reverse(url_name))
            self.assertEqual(r.status_code, 200, f'{url_name} failed')
