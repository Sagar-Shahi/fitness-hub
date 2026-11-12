from datetime import date, timedelta
from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from . import analytics
from .models import Profile, profile_for
from .testutils import days_ago, make_meal, make_user, make_weight, make_workout


class HelperTests(SimpleTestCase):
    def test_nice_ceiling(self):
        cases = {0: 4, 4: 4, 5: 5, 6: 10, 11: 20, 21: 50, 51: 100, 999: 1000, 2301: 5000}
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(analytics.nice_ceiling(value), expected)

    def test_week_starts_on_monday(self):
        self.assertEqual(analytics.week_start(date(2026, 11, 12)), date(2026, 11, 9))  # Thursday
        self.assertEqual(analytics.week_start(date(2026, 11, 9)), date(2026, 11, 9))
        self.assertEqual(analytics.week_start(date(2026, 11, 15)), date(2026, 11, 9))  # Sunday

    def test_percent_is_clamped(self):
        self.assertEqual(analytics.percent(1, 4), 25)
        self.assertEqual(analytics.percent(9, 4), 100)
        self.assertEqual(analytics.percent(-3, 4), 0)
        self.assertEqual(analytics.percent(3, 0), 0)


class SeriesTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_workouts_per_day_fills_quiet_days(self):
        make_workout(self.user, ago=0)
        make_workout(self.user, ago=0, name='Second')
        make_workout(self.user, ago=2)
        make_workout(self.user, ago=40)
        series = analytics.workouts_per_day(self.user, 7)
        self.assertEqual([n for _, n in series], [0, 0, 0, 0, 1, 0, 2])
        self.assertEqual(series[-1][0], timezone.localdate())

    def test_calories_are_summed_per_day(self):
        make_meal(self.user, ago=0, calories=500)
        make_meal(self.user, ago=0, calories=300)
        make_meal(self.user, ago=1, calories=700)
        self.assertEqual([n for _, n in analytics.calories_per_day(self.user, 3)], [0, 700, 800])

    def test_other_users_data_is_never_included(self):
        other = make_user('other')
        make_workout(other); make_meal(other); make_weight(other)
        self.assertEqual(sum(n for _, n in analytics.workouts_per_day(self.user, 7)), 0)
        self.assertEqual(sum(n for _, n in analytics.calories_per_day(self.user, 7)), 0)
        self.assertEqual(analytics.weight_points(self.user, 30), [])

    def test_day_totals(self):
        make_meal(self.user, calories=500, protein=30, carbs=50, fat=10)
        make_meal(self.user, calories=250, protein=10, carbs=20, fat=5)
        self.assertEqual(analytics.day_totals(self.user, timezone.localdate()),
                         {'calories': 750, 'protein': 40, 'carbs': 70, 'fat': 15})
        self.assertEqual(analytics.day_totals(self.user, days_ago(5)), {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0})


class StreakTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_no_workouts(self):
        self.assertEqual(analytics.streak(self.user), 0)

    def test_counts_consecutive_days_ending_today(self):
        for ago in (0, 1, 2, 4):
            make_workout(self.user, ago=ago)
        self.assertEqual(analytics.streak(self.user), 3)

    def test_a_streak_survives_until_the_end_of_today(self):
        for ago in (1, 2):
            make_workout(self.user, ago=ago)
        self.assertEqual(analytics.streak(self.user), 2)

    def test_a_gap_of_a_full_day_breaks_it(self):
        make_workout(self.user, ago=2)
        self.assertEqual(analytics.streak(self.user), 0)


class DashboardDataTests(TestCase):
    def test_week_numbers_and_weight_change(self):
        user = make_user()
        profile = Profile.objects.create(owner=user, calorie_target=2000, weekly_workout_target=3)
        make_workout(user, ago=0, minutes=30)
        make_workout(user, ago=0, minutes=40, name='B')
        make_meal(user, calories=600)
        make_weight(user, ago=20, kg='82.0')
        make_weight(user, ago=0, kg='80.5')
        data = analytics.dashboard(user, profile)
        self.assertEqual((data['week_done'], data['week_target'], data['week_minutes']), (2, 3, 70))
        self.assertEqual((data['today']['calories'], data['calorie_left']), (600, 1400))
        self.assertEqual(data['latest_weight'].weight_kg, Decimal('80.5'))
        self.assertEqual(data['weight_change'], Decimal('-1.5'))

    def test_a_fresh_account_has_zeroes_not_errors(self):
        user = make_user()
        data = analytics.dashboard(user, profile_for(user))
        self.assertEqual((data['week_done'], data['streak'], data['latest_weight'], data['weight_change']), (0, 0, None, None))
        self.assertEqual(data['calorie_left'], 2200)


class ChartTests(SimpleTestCase):
    def _series(self, counts):
        today = timezone.localdate()
        return [(today - timedelta(days=len(counts) - 1 - i), n) for i, n in enumerate(counts)]

    def test_bar_geometry(self):
        chart = analytics.bar_chart(self._series([0, 5, 10]), 'workouts', width=300, height=100)
        self.assertEqual((len(chart['bars']), chart['axis_max'], chart['total']), (3, 10, 15))
        heights = [float(b['h']) for b in chart['bars']]
        self.assertEqual(heights[0], 0)
        self.assertAlmostEqual(heights[1] * 2, heights[2], delta=0.2)
        for bar in chart['bars']:
            self.assertGreaterEqual(float(bar['x']), chart['left'])
            self.assertLessEqual(float(bar['x']) + float(bar['w']), chart['right_edge'])

    def test_empty_bar_chart_still_has_an_axis(self):
        chart = analytics.bar_chart(self._series([0] * 14), 'kcal')
        self.assertEqual((chart['axis_max'], chart['total']), (4, 0))

    def test_line_chart_with_no_points(self):
        self.assertTrue(analytics.line_chart([])['empty'])

    def test_line_chart_with_one_point(self):
        chart = analytics.line_chart([(date(2026, 11, 1), Decimal('80.0'))])
        self.assertFalse(chart['empty'])
        self.assertEqual(len(chart['dots']), 1)
        self.assertTrue(chart['path'].startswith('M'))

    def test_line_goes_down_when_weight_goes_down(self):
        chart = analytics.line_chart([(date(2026, 11, 1), Decimal('82')), (date(2026, 11, 10), Decimal('80'))])
        first, last = chart['dots']
        self.assertLess(float(first['x']), float(last['x']))
        self.assertLess(float(first['y']), float(last['y']))  # SVG y grows downward: lower weight is lower on screen

    def test_target_line_is_drawn_and_kept_in_range(self):
        chart = analytics.line_chart([(date(2026, 11, 1), Decimal('82')), (date(2026, 11, 10), Decimal('81'))], target=Decimal('75'))
        self.assertIsNotNone(chart['target_y'])
        self.assertLessEqual(float(chart['target_y']), chart['height'])
        self.assertGreaterEqual(float(chart['target_y']), 0)

    def test_numbers_are_printable_strings(self):
        chart = analytics.line_chart([(date(2026, 11, 1), Decimal('82.3')), (date(2026, 11, 5), Decimal('81.9'))])
        for dot in chart['dots']:
            self.assertNotIn(',', dot['x'] + dot['y'])
