from typing import Optional, Dict, Any
from datetime import date


ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

ACTIVITY_LABELS = {
    'sedentary': 'Sedentary',
    'light': 'Lightly Active',
    'moderate': 'Moderately Active',
    'active': 'Very Active',
    'very_active': 'Very Active',
}

GOAL_ADJUSTMENTS = {
    'lose_weight': -500,
    'fat_loss': -500,
    'maintenance': 0,
    'general': 0,
    'gain_muscle': 300,
    'muscle_gain': 300,
    'lean_bulk': 350,
    'lean_athletic': 200,
    'recomp': -150,
    'strength': 250,
    'calisthenics': 150,
}

MACRO_SPLITS = {
    'ectomorph': {'protein': 0.25, 'carbs': 0.55, 'fats': 0.20},
    'mesomorph': {'protein': 0.30, 'carbs': 0.45, 'fats': 0.25},
    'endomorph': {'protein': 0.35, 'carbs': 0.35, 'fats': 0.30},
}

PROTEIN_PER_KG = {
    'lose_weight': 2.2,
    'fat_loss': 2.2,
    'gain_muscle': 2.0,
    'muscle_gain': 2.0,
    'lean_bulk': 1.8,
    'maintenance': 1.6,
    'general': 1.6,
    'recomp': 2.0,
    'strength': 1.8,
    'calisthenics': 1.8,
    'lean_athletic': 1.8,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    if sex == 'male':
        return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return bmr * multiplier


def calculate_target_calories(tdee: float, goal: str) -> int:
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    return int(round(tdee + adjustment))


def calculate_macros(target_calories: int, weight_kg: float, body_type: str, goal: str) -> Dict[str, int]:
    split = MACRO_SPLITS.get(body_type, MACRO_SPLITS['mesomorph'])
    protein_per_kg = PROTEIN_PER_KG.get(goal, 1.6)

    protein_g = int(round(weight_kg * protein_per_kg))
    fats_pct = split['fats']
    carbs_pct = split['carbs']

    fats_g = int(round((target_calories * fats_pct) / 9))
    carbs_g = int(round((target_calories * carbs_pct) / 4))

    return {
        'protein': protein_g,
        'carbs': carbs_g,
        'fats': fats_g,
    }


def generate_nutrition_plan(profile, weight_kg: Optional[float] = None, height_cm: Optional[float] = None,
                            age: Optional[int] = None, sex: Optional[str] = None,
                            activity_level: Optional[str] = None, goal: Optional[str] = None) -> Dict[str, Any]:
    weight_kg = weight_kg or getattr(profile, 'weight_kg', None)
    height_cm = height_cm or getattr(profile, 'height_cm', None)
    age = age or getattr(profile, 'age', None)
    sex = sex or getattr(profile, 'gender', 'male')
    activity_level = activity_level or getattr(profile, 'activity_level', 'moderate')
    goal = goal or getattr(profile, 'selected_goal', 'general')

    if not all([weight_kg, height_cm, age]):
        return {
            'ready': False,
            'error': 'Please complete your profile with age, weight, and height to get a nutrition plan.',
        }

    weight_kg = float(weight_kg)
    height_cm = float(height_cm)
    age = int(age)

    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    target_calories = calculate_target_calories(tdee, goal)

    body_type = getattr(profile, 'body_type', 'mesomorph') or 'mesomorph'
    macros = calculate_macros(target_calories, weight_kg, body_type, goal)

    body_type_name = {
        'lean': 'Ectomorph',
        'average': 'Mesomorph',
        'stocky': 'Endomorph',
    }.get(body_type, body_type.title())

    goal_name = goal.replace('_', ' ').title() if goal else 'Maintenance'
    activity_name = ACTIVITY_LABELS.get(activity_level, activity_level.title())

    notes = (
        f"Targets calculated for a {age}-year-old {sex} ({body_type_name}) at "
        f"{weight_kg} kg, {height_cm} cm, {activity_name.lower()}, "
        f"with a {goal_name} goal. "
        f"BMR: {int(round(bmr))} kcal -> TDEE: {int(round(tdee))} kcal -> "
        f"Target: {target_calories} kcal. "
        f"Macros split: {round(macros['protein'] / weight_kg, 2)} g/kg protein for muscle preservation, "
        f"{int(macros['carbs'] * 4 / target_calories * 100)}% carbs for energy, "
        f"{int(macros['fats'] * 9 / target_calories * 100)}% fats for hormones."
    )

    return {
        'ready': True,
        'bmr': int(round(bmr)),
        'tdee': int(round(tdee)),
        'calories': target_calories,
        'protein': macros['protein'],
        'carbs': macros['carbs'],
        'fats': macros['fats'],
        'notes': notes,
        'goal_name': goal_name,
        'body_type_name': body_type_name,
        'activity_name': activity_name,
        'today': date.today().isoformat(),
    }
