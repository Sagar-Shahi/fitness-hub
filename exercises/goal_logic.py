"""
Goal-based filtering and nutrition logic for exercises and meal plans.
"""
from typing import List, Dict


def filter_exercises_by_goal(exercises: List[Dict], selected_goal: str, focus_areas: list = None) -> List[Dict]:
    """Return a filtered list of exercises relevant to the selected goal.

    - 'calisthenics': prioritize bodyweight moves and progressions
    - 'lean_athletic': prioritize upper-body and core shaping work
    - 'weight_loss': prioritize conditioning and leg-focused calorie burners
    - 'strength' / 'muscle_gain' / 'lean_bulk' / 'recomp': prioritize strength and hypertrophy
    - focus_areas: further prioritize category matches if provided
    """
    key = (selected_goal or '').lower()
    if not exercises:
        return []

    def is_bodyweight(ex):
        eq = (ex.get('equipment') or '').lower()
        return eq in ('', 'bodyweight', 'none')

    if key.startswith('calisthenics'):
        results = [e for e in exercises if is_bodyweight(e) or 'progression' in e.get('name', '').lower()]
        if not results:
            results = [e for e in exercises if is_bodyweight(e)]
    elif key.startswith('v_taper') or key.startswith('lean_athletic'):
        results = [
            e for e in exercises
            if e.get('category') in ('back', 'shoulders', 'core', 'legs')
            or 'row' in e.get('name', '').lower()
            or 'pull' in e.get('name', '').lower()
        ]
    elif key.startswith('weight_loss') or key.startswith('fat_loss'):
        results = [
            e for e in exercises
            if e.get('category') in ('cardio', 'legs', 'core')
            or 'hiit' in e.get('name', '').lower()
            or 'conditioning' in e.get('name', '').lower()
        ]
    elif key.startswith('strength') or key.startswith('muscle_gain') or key.startswith('lean_bulk') or key.startswith('recomp'):
        results = [
            e for e in exercises
            if e.get('goal') in ('strength', 'hypertrophy')
            or e.get('category') in ('legs', 'back', 'chest', 'shoulders', 'core')
        ]
    else:
        results = exercises

    focus_map = {
        'shoulders': 'shoulders',
        'back': 'back',
        'core': 'core',
        'legs': 'legs',
    }
    focus_filters = [focus_map.get(area.lower()) for area in (focus_areas or []) if focus_map.get(area.lower())]
    if focus_filters:
        focused = [e for e in results if e.get('category') in focus_filters]
        if focused:
            return focused

    return results


def adjust_reps_sets_for_body_type(reps: int, sets: int, body_type: str) -> Dict:
    """Adjust base reps/sets according to user's body type/recovery capacity.

    - 'lean': slightly higher reps, moderate sets
    - 'average': no change
    - 'stocky': slightly lower reps, fewer sets
    """
    bt = (body_type or '').lower()
    if bt == 'lean':
        return {'reps': max(1, int(reps * 1.15)), 'sets': max(1, int(sets * 1.0))}
    if bt == 'stocky':
        return {'reps': max(1, int(reps * 0.85)), 'sets': max(1, int(sets * 0.85))}
    return {'reps': reps, 'sets': sets}


def generate_macros_for_goal(goal: str, weight_kg: float = None) -> Dict:
    """Return macronutrient ratio guidance for a given goal.

    Returns percent composition and suggestions for grams per kg if weight is provided.
    """
    g = (goal or '').lower()
    if g.startswith('calisthenics'):
        # Lean muscle maintenance, slightly higher protein
        ratio = {'protein_pct': 30, 'carbs_pct': 45, 'fat_pct': 25}
        note = 'Prioritize high-quality protein sources for recovery (eggs, legumes, lean fish).'
    elif g.startswith('weight_loss'):
        ratio = {'protein_pct': 35, 'carbs_pct': 35, 'fat_pct': 30}
        note = 'Higher protein and controlled carbs to support fat loss while preserving muscle.'
    elif g.startswith('v_taper'):
        ratio = {'protein_pct': 28, 'carbs_pct': 44, 'fat_pct': 28}
        note = 'Balanced macros to support hypertrophy in upper-body pulling/pushing movements.'
    else:
        ratio = {'protein_pct': 25, 'carbs_pct': 50, 'fat_pct': 25}
        note = 'General balanced macro distribution.'

    out = {'ratio': ratio, 'note': note}
    if weight_kg:
        # rough grams per kg recommendations
        protein_gpk = 1.6
        if g.startswith('weight_loss'):
            protein_gpk = 1.8
        out['protein_g_per_kg'] = round(protein_gpk, 2)
        out['protein_grams'] = int(protein_gpk * weight_kg)
    return out


def meal_suggestions_for_goal(goal: str) -> List[Dict]:
    """Return simple meal suggestions tailored to goal."""
    g = (goal or '').lower()
    if g.startswith('calisthenics'):
        return [
            {'title': 'Egg & Spinach Scramble', 'notes': 'High-quality protein, iron for recovery.'},
            {'title': 'Chickpea & Quinoa Bowl', 'notes': 'Plant protein, complex carbs, high fiber.'},
            {'title': 'Greek Yogurt + Berries', 'notes': 'Protein-rich snack for muscle repair.'},
        ]
    if g.startswith('weight_loss'):
        return [
            {'title': 'Grilled Chicken Salad', 'notes': 'High protein, low-calorie vegetables.'},
            {'title': 'Lentil Soup', 'notes': 'Filling fiber and plant protein.'},
        ]
    return [
        {'title': 'Oatmeal with Nuts & Fruit', 'notes': 'Balanced breakfast option.'},
    ]
