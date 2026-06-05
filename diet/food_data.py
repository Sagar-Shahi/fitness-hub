"""Affordable food database and budget meal presets for the Diet app."""
from typing import Dict, List, Any


AFFORDABLE_FOODS: Dict[str, List[Dict[str, Any]]] = {
    'protein': [
        {'name': 'Eggs', 'serving': '2 large eggs', 'protein': 12, 'carbs': 1, 'fats': 10, 'calories': 155, 'cost': 0.50},
        {'name': 'Chicken Breast (budget)', 'serving': '100g', 'protein': 31, 'carbs': 0, 'fats': 3, 'calories': 165, 'cost': 1.50},
        {'name': 'Canned Tuna', 'serving': '100g', 'protein': 26, 'carbs': 0, 'fats': 1, 'calories': 112, 'cost': 0.80},
        {'name': 'Lentils (cooked)', 'serving': '100g', 'protein': 9, 'carbs': 20, 'fats': 0.4, 'calories': 116, 'cost': 0.30},
        {'name': 'Beans (canned)', 'serving': '100g', 'protein': 8, 'carbs': 15, 'fats': 0.3, 'calories': 92, 'cost': 0.25},
        {'name': 'Greek Yogurt', 'serving': '150g', 'protein': 15, 'carbs': 6, 'fats': 3, 'calories': 110, 'cost': 0.80},
    ],
    'carbs': [
        {'name': 'Rice (white)', 'serving': '100g cooked', 'protein': 2.7, 'carbs': 28, 'fats': 0.3, 'calories': 130, 'cost': 0.15},
        {'name': 'Oats', 'serving': '50g', 'protein': 5, 'carbs': 27, 'fats': 3, 'calories': 150, 'cost': 0.30},
        {'name': 'Sweet Potato', 'serving': '100g', 'protein': 1.6, 'carbs': 20, 'fats': 0.1, 'calories': 86, 'cost': 0.40},
        {'name': 'Banana', 'serving': '1 medium', 'protein': 1.3, 'carbs': 27, 'fats': 0.3, 'calories': 105, 'cost': 0.20},
        {'name': 'Pasta', 'serving': '100g cooked', 'protein': 4, 'carbs': 25, 'fats': 0.7, 'calories': 131, 'cost': 0.25},
        {'name': 'Bread', 'serving': '2 slices', 'protein': 8, 'carbs': 40, 'fats': 2, 'calories': 210, 'cost': 0.35},
    ],
    'fats': [
        {'name': 'Olive Oil', 'serving': '1 tbsp (15ml)', 'protein': 0, 'carbs': 0, 'fats': 14, 'calories': 120, 'cost': 0.20},
        {'name': 'Peanut Butter', 'serving': '2 tbsp', 'protein': 8, 'carbs': 7, 'fats': 16, 'calories': 188, 'cost': 0.40},
        {'name': 'Almonds', 'serving': '25g', 'protein': 6, 'carbs': 6, 'fats': 14, 'calories': 160, 'cost': 0.60},
        {'name': 'Coconut Oil', 'serving': '1 tbsp', 'protein': 0, 'carbs': 0, 'fats': 14, 'calories': 120, 'cost': 0.35},
    ],
    'vegetables': [
        {'name': 'Broccoli', 'serving': '100g', 'protein': 2.8, 'carbs': 7, 'fats': 0.4, 'calories': 34, 'cost': 0.50},
        {'name': 'Spinach', 'serving': '100g', 'protein': 2.7, 'carbs': 3.6, 'fats': 0.4, 'calories': 23, 'cost': 0.40},
        {'name': 'Carrots', 'serving': '100g', 'protein': 0.9, 'carbs': 10, 'fats': 0.2, 'calories': 41, 'cost': 0.25},
    ],
}


BUDGET_MEALS: List[Dict[str, Any]] = [
    {
        'name': 'Budget Breakfast',
        'items': ['2 Eggs', 'Toast (2 slices)', '1 Banana'],
        'total_protein': 15, 'total_carbs': 67, 'total_fats': 12, 'total_calories': 430, 'total_cost': 1.05,
    },
    {
        'name': 'Quick Lunch',
        'items': ['Canned Tuna (100g)', 'Rice (100g cooked)', 'Spinach (50g)'],
        'total_protein': 29, 'total_carbs': 32, 'total_fats': 2, 'total_calories': 270, 'total_cost': 1.55,
    },
    {
        'name': 'Budget Dinner',
        'items': ['Beans (100g)', 'Rice (100g cooked)', 'Carrots (100g)'],
        'total_protein': 14, 'total_carbs': 49, 'total_fats': 1, 'total_calories': 280, 'total_cost': 0.65,
    },
    {
        'name': 'Protein Snack',
        'items': ['Greek Yogurt (150g)', 'Oats (30g)'],
        'total_protein': 16, 'total_carbs': 22, 'total_fats': 3, 'total_calories': 208, 'total_cost': 0.88,
    },
]


def daily_totals(meals: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        'total_protein': round(sum(m['total_protein'] for m in meals), 1),
        'total_carbs': round(sum(m['total_carbs'] for m in meals), 1),
        'total_fats': round(sum(m['total_fats'] for m in meals), 1),
        'total_calories': sum(m['total_calories'] for m in meals),
        'total_cost': round(sum(m['total_cost'] for m in meals), 2),
    }
