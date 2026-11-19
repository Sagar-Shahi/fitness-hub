from decimal import Decimal
from django.test import TestCase

from .models import Profile, BodyMetric
from .nutrition import calculate_nutrition_targets
from django.urls import reverse

from .testutils import make_user


class PersonalizedNutritionTests(TestCase):
    def setUp(self):
        self.user = make_user('nutrition-user')
        self.client.force_login(self.user)
        self.profile = Profile.objects.create(
            owner=self.user,
            age=25,
            height_cm=Decimal('175'),
            starting_weight_kg=Decimal('75'),
            sex_for_calculation='male',
            activity_level='moderate',
            training_type='strength',
            nutrition_goal='maintain',
        )

    def test_returns_personalized_calorie_and_macro_targets(self):
        result = calculate_nutrition_targets(self.profile)
        self.assertIsNotNone(result)
        self.assertGreater(result['calories'], 1400)
        self.assertEqual(result['protein_g'], 135)
        self.assertEqual(result['fat_g'], 60)
        self.assertGreaterEqual(result['carbs_g'], 0)
        self.assertEqual(result['goal_label'], 'Weight maintenance')

    def test_uses_latest_logged_weight_over_starting_weight(self):
        BodyMetric.objects.create(owner=self.profile.owner, weight_kg=Decimal('80'))
        result = calculate_nutrition_targets(self.profile, Decimal('80'))
        self.assertEqual(result['protein_g'], 144)

    def test_minor_is_not_given_a_calorie_prescription(self):
        self.profile.age = 17
        self.assertIn('reason', calculate_nutrition_targets(self.profile))

    def test_minor_is_not_given_a_target_even_with_incomplete_profile(self):
        self.profile.age = 17
        self.profile.height_cm = None
        self.assertIn('reason', calculate_nutrition_targets(self.profile))

    def test_incomplete_profile_does_not_make_up_targets(self):
        self.profile.height_cm = None
        self.assertIsNone(calculate_nutrition_targets(self.profile))

    def test_macro_targets_are_not_returned_when_they_exceed_calorie_estimate(self):
        self.profile.age = 18
        self.profile.height_cm = Decimal('120')
        self.profile.starting_weight_kg = Decimal('300')
        self.profile.sex_for_calculation = 'male'
        self.profile.activity_level = 'sedentary'
        self.profile.training_type = 'strength'
        self.profile.nutrition_goal = 'fat_loss'
        self.profile.body_fat_percentage = Decimal('2')
        self.assertIn('reason', calculate_nutrition_targets(self.profile))

    def test_extreme_calorie_estimate_is_not_displayed(self):
        self.profile.age = 99
        self.profile.height_cm = Decimal('120')
        self.profile.starting_weight_kg = Decimal('30')
        self.profile.activity_level = 'sedentary'
        self.profile.nutrition_goal = 'fat_loss'
        self.assertIn('reason', calculate_nutrition_targets(self.profile))

    def test_goals_form_saves_profile_and_personalized_calorie_target(self):
        response = self.client.post(reverse('tracker:goals'), {
            'age': '25',
            'sex_for_calculation': 'male',
            'height_cm': '175',
            'starting_weight_kg': '75',
            'activity_level': 'moderate',
            'training_type': 'strength',
            'nutrition_goal': 'muscle_gain',
            'calorie_target': '2200',
            'weekly_workout_target': '4',
            'target_weight_kg': '',
        })
        self.assertRedirects(response, reverse('tracker:dashboard'))
        profile = Profile.objects.get(owner=self.user)
        self.assertGreater(profile.calorie_target, 2200)
        self.assertEqual(profile.nutrition_goal, 'muscle_gain')

    def test_minor_does_not_see_a_fallback_calorie_input_on_goals_page(self):
        self.profile.age = 17
        self.profile.save()
        response = self.client.get(reverse('tracker:goals'))
        self.assertNotContains(response, 'Fallback daily calorie target (kcal)')
        self.assertContains(response, 'Calorie and macro prescriptions are not shown for under-18 profiles')

    def test_minor_does_not_see_a_calorie_target_on_meals_page(self):
        self.profile.age = 17
        self.profile.save()
        response = self.client.get(reverse('tracker:meals'))
        self.assertIsNone(response.context['target'])
        self.assertContains(response, 'Personalized calorie targets are only calculated for adults.')
        self.assertNotContains(response, '2200 kcal daily goal')

    def test_unsafe_estimate_is_not_shown_as_a_fallback_target(self):
        self.profile.age = 99
        self.profile.height_cm = Decimal('120')
        self.profile.starting_weight_kg = Decimal('30')
        self.profile.activity_level = 'sedentary'
        self.profile.nutrition_goal = 'fat_loss'
        self.profile.save()
        meals = self.client.get(reverse('tracker:meals'))
        self.assertIsNone(meals.context['target'])
        self.assertContains(meals, 'falls outside FitHub')
        dashboard = self.client.get(reverse('tracker:dashboard'))
        self.assertIsNone(dashboard.context['d']['calorie_target'])

    def test_dashboard_does_not_show_a_calorie_target_for_a_minor(self):
        self.profile.age = 17
        self.profile.save()
        response = self.client.get(reverse('tracker:dashboard'))
        self.assertIsNone(response.context['d']['calorie_target'])
        self.assertContains(response, 'Personalized calorie targets are only calculated for adults.')

    def test_meals_page_uses_personalized_calorie_and_macro_targets(self):
        self.profile.calorie_target = 2200
        self.profile.save()
        BodyMetric.objects.create(owner=self.user, weight_kg=Decimal('80'))
        response = self.client.get(reverse('tracker:meals'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['nutrition_plan'])
        self.assertEqual(response.context['target'], response.context['nutrition_plan']['calories'])
        self.assertEqual(response.context['macro_remaining']['protein'], response.context['nutrition_plan']['protein_g'])
        self.assertContains(response, 'PERSONALIZED DAILY TARGETS')

    def test_body_fat_is_optional_and_uses_lean_mass_for_protein(self):
        self.profile.body_fat_percentage = Decimal('20')
        result = calculate_nutrition_targets(self.profile)
        self.assertTrue(result['body_composition_used'])
        self.assertEqual(result['lean_mass_kg'], 60)
        self.assertEqual(result['protein_g'], 120)

    def test_body_type_does_not_change_calorie_estimate(self):
        baseline = calculate_nutrition_targets(self.profile)
        self.profile.body_type = 'ectomorph'
        with_type = calculate_nutrition_targets(self.profile)
        self.assertEqual(baseline['calories'], with_type['calories'])

    def test_body_composition_fields_can_be_left_blank(self):
        self.profile.body_type = ''
        self.profile.body_fat_percentage = None
        self.profile.waist_cm = None
        self.profile.muscle_mass_kg = None
        result = calculate_nutrition_targets(self.profile)
        self.assertFalse(result['body_composition_used'])
        self.assertEqual(result['protein_g'], 135)
