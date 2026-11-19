"""Evidence-informed, transparent nutrition estimates for adult FitHub members."""
from decimal import Decimal, ROUND_HALF_UP

ACTIVITY_FACTORS = {
    'sedentary': Decimal('1.20'),
    'light': Decimal('1.375'),
    'moderate': Decimal('1.55'),
    'very_active': Decimal('1.725'),
}
GOALS = {
    'fat_loss': ('Fat loss', -250),
    'maintain': ('Weight maintenance', 0),
    'muscle_gain': ('Muscle gain', 200),
}
PROTEIN_FACTORS = {
    'strength': Decimal('1.8'),
    'cardio': Decimal('1.4'),
    'mixed': Decimal('1.7'),
    'general': Decimal('1.6'),
}


def _whole(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def calculate_nutrition_targets(profile, weight_kg=None):
    """Return daily estimates or a clear reason when the profile is not suitable."""
    required = (
        profile.age, profile.height_cm, profile.sex_for_calculation,
        profile.activity_level, profile.training_type,
    )
    if any(value in (None, '') for value in required):
        return None
    if profile.age < 18:
        return {'reason': 'Personalized calorie targets are only calculated for adults. Please seek age-appropriate guidance from a qualified professional.'}
    weight = weight_kg or profile.starting_weight_kg
    if not weight:
        return None
    if profile.activity_level not in ACTIVITY_FACTORS or profile.training_type not in PROTEIN_FACTORS:
        return None
    weight = Decimal(str(weight))
    height = Decimal(str(profile.height_cm))
    age = Decimal(profile.age)
    # Mifflin-St Jeor BMR. For "other / prefer not to say", use the midpoint
    # between the published male and female constants and disclose that estimate.
    base = Decimal('5') if profile.sex_for_calculation == 'male' else (
        Decimal('-161') if profile.sex_for_calculation == 'female' else Decimal('-78')
    )
    bmr = Decimal('10') * weight + Decimal('6.25') * height - Decimal('5') * age + base
    maintenance = bmr * ACTIVITY_FACTORS[profile.activity_level]
    goal_label, adjustment = GOALS.get(profile.nutrition_goal, GOALS['maintain'])
    calories = _whole(maintenance + Decimal(adjustment))
    # Avoid presenting very low or implausibly high calorie prescriptions.
    if calories < 1400 or calories > 5000:
        return {'reason': 'Your calculated energy estimate falls outside FitHub’s safe display range. Please ask a registered dietitian or healthcare professional to set an appropriate target.'}
    if profile.body_fat_percentage is not None:
        # Use estimated lean mass for protein when a user supplies body-fat data.
        # The body-fat figure is optional and does not alter the Mifflin calorie estimate.
        lean_mass = weight * (Decimal('1') - Decimal(str(profile.body_fat_percentage)) / Decimal('100'))
        lean_factors = {
            'strength': Decimal('2.0'),
            'cardio': Decimal('1.6'),
            'mixed': Decimal('1.8'),
            'general': Decimal('1.6'),
        }
        protein = _whole(lean_mass * lean_factors[profile.training_type])
    else:
        lean_mass = None
        protein = _whole(weight * PROTEIN_FACTORS[profile.training_type])
    fat = _whole(weight * Decimal('0.8'))
    macro_calories = protein * 4 + fat * 9
    if macro_calories > calories:
        return {'reason': 'The estimated calorie target cannot support the calculated protein and fat amounts. Please ask a registered dietitian or healthcare professional for an appropriate plan.'}
    carbs = max(0, _whole((Decimal(calories) - macro_calories) / 4))
    return {
        'calories': calories,
        'maintenance_calories': _whole(maintenance),
        'protein_g': protein,
        'lean_mass_kg': _whole(lean_mass) if lean_mass is not None else None,
        'body_composition_used': lean_mass is not None,
        'carbs_g': carbs,
        'fat_g': fat,
        'goal_label': goal_label,
        'method': 'Mifflin-St Jeor BMR with an activity multiplier',
        'protein_method': 'Estimated lean mass' if lean_mass is not None else 'Current body weight',
    }


def refresh_profile_calorie_target(profile):
    """Keep the saved dashboard/API target aligned with the latest recorded body weight."""
    from .models import BodyMetric

    latest_weight = BodyMetric.objects.filter(owner=profile.owner).first()
    current_weight = latest_weight.weight_kg if latest_weight else profile.starting_weight_kg
    plan = calculate_nutrition_targets(profile, current_weight)
    if plan and plan.get('calories'):
        profile.calorie_target = plan['calories']
        profile.save(update_fields=['calorie_target'])
    return current_weight, plan
