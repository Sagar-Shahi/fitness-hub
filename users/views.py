from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .forms import UserUpdateForm, ProfileForm

# Affordable food database
AFFORDABLE_FOODS = {
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

BUDGET_MEALS = [
    {
        'name': 'Budget Breakfast',
        'items': ['2 Eggs', 'Toast (2 slices)', '1 Banana'],
        'total_protein': 15,
        'total_carbs': 67,
        'total_fats': 12,
        'total_calories': 430,
        'total_cost': 1.05,
    },
    {
        'name': 'Quick Lunch',
        'items': ['Canned Tuna (100g)', 'Rice (100g cooked)', 'Spinach (50g)'],
        'total_protein': 29,
        'total_carbs': 32,
        'total_fats': 2,
        'total_calories': 270,
        'total_cost': 1.55,
    },
    {
        'name': 'Budget Dinner',
        'items': ['Beans (100g)', 'Rice (100g cooked)', 'Carrots (100g)'],
        'total_protein': 14,
        'total_carbs': 49,
        'total_fats': 1,
        'total_calories': 280,
        'total_cost': 0.65,
    },
    {
        'name': 'Protein Snack',
        'items': ['Greek Yogurt (150g)', 'Oats (30g)'],
        'total_protein': 16,
        'total_carbs': 22,
        'total_fats': 3,
        'total_calories': 208,
        'total_cost': 0.88,
    },
]

def calculate_nutrition(age, weight, height, gender, activity_level, body_type):
    """Calculate BMR and daily calorie recommendation"""
    # Harris-Benedict formula for BMR
    if gender == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Activity multipliers
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9,
    }
    
    daily_calories = bmr * activity_multipliers.get(activity_level, 1.55)
    
    # Macro suggestions based on body type
    macro_splits = {
        'ectomorph': {'protein': 0.30, 'carbs': 0.50, 'fats': 0.20},  # Lean/skinny
        'mesomorph': {'protein': 0.35, 'carbs': 0.45, 'fats': 0.20},  # Athletic
        'endomorph': {'protein': 0.35, 'carbs': 0.40, 'fats': 0.25},  # Curvy/stocky
    }
    
    macros = macro_splits.get(body_type, macro_splits['mesomorph'])
    
    return {
        'bmr': round(bmr, 1),
        'daily_calories': round(daily_calories, 0),
        'protein_g': round((daily_calories * macros['protein']) / 4, 1),
        'carbs_g': round((daily_calories * macros['carbs']) / 4, 1),
        'fats_g': round((daily_calories * macros['fats']) / 9, 1),
        'protein_pct': int(macros['protein'] * 100),
        'carbs_pct': int(macros['carbs'] * 100),
        'fats_pct': int(macros['fats'] * 100),
    }


@login_required
def profile(request):
    return render(request, 'users/profile.html')


@login_required
def edit_profile(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        uform = UserUpdateForm(request.POST, instance=user)
        pform = ProfileForm(request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        uform = UserUpdateForm(instance=user)
        pform = ProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'uform': uform, 'pform': pform})


@login_required
def exercise_records(request):
    records = [
        {'date': '2026-06-01', 'workout': 'Full-Body Strength', 'duration': '32 mins', 'calories': 420},
        {'date': '2026-05-30', 'workout': 'HIIT Conditioning', 'duration': '20 mins', 'calories': 365},
        {'date': '2026-05-28', 'workout': 'Recovery Stretch', 'duration': '18 mins', 'calories': 120},
    ]
    return render(request, 'users/exercise_records.html', {'records': records})


@login_required
def purchase_history(request):
    purchases = [
        {'date': '2026-05-25', 'item': 'Whey Protein Powder', 'amount': '$34.99'},
        {'date': '2026-05-18', 'item': 'Pro Dumbbell Set', 'amount': '$59.99'},
    ]
    return render(request, 'users/purchase_history.html', {'purchases': purchases})


@login_required
def nutrition_tracker(request):
    return render(request, 'users/nutrition_tracker.html', {'affordable_foods': AFFORDABLE_FOODS})


@login_required
def budget_meals(request):
    return render(request, 'users/budget_meals.html', {'meals': BUDGET_MEALS})


@login_required
def nutrition_calculator(request):
    if request.method == 'POST':
        try:
            age = int(request.POST.get('age', 25))
            weight = float(request.POST.get('weight', 70))
            height = float(request.POST.get('height', 175))
            gender = request.POST.get('gender', 'male')
            activity = request.POST.get('activity_level', 'moderate')
            body_type = request.POST.get('body_type', 'mesomorph')
            
            nutrition = calculate_nutrition(age, weight, height, gender, activity, body_type)
            
            return render(request, 'users/nutrition_results.html', {'nutrition': nutrition})
        except (ValueError, TypeError):
            messages.error(request, 'Please enter valid numbers for all fields.')
    
    return render(request, 'users/nutrition_calculator.html')


def about(request):
    return render(request, 'about.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'users/register.html', {'form': form})
