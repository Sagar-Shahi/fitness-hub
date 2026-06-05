from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.utils import sync_goal_from_profile

from .forms import (
    AccountSettingsForm,
    GoalSelectionForm,
    ProfileForm,
    StyledPasswordChangeForm,
    UserRegistrationForm,
    UserUpdateForm,
)
from .models import Profile


@login_required
def profile(request):
    return render(request, 'users/profile.html')


@login_required
def settings_hub(request):
    """Landing page for all account / security / profile settings."""
    user = request.user
    profile = getattr(user, 'profile', None)
    context = {
        'user_obj': user,
        'profile_obj': profile,
        'has_email': bool(user.email),
        'has_full_name': bool(user.get_full_name()),
    }
    return render(request, 'users/settings_hub.html', context)


@login_required
def settings_account(request):
    """Edit username, first name, last name, email."""
    user = request.user
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, instance=user, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account details updated.')
            return redirect('settings-account')
    else:
        form = AccountSettingsForm(instance=user, user=user)

    return render(request, 'users/settings_account.html', {'form': form})


@login_required
def settings_password(request):
    """Change password using Django's PasswordChangeForm."""
    user = request.user
    if request.method == 'POST':
        form = StyledPasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('settings-password')
    else:
        form = StyledPasswordChangeForm(user)

    return render(request, 'users/settings_password.html', {'form': form})


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
    from exercises.models import ExerciseCompletion
    from collections import OrderedDict
    from django.db.models import Sum

    completions = (
        ExerciseCompletion.objects
        .filter(user=request.user)
        .select_related('exercise')
        .order_by('-date', '-id')
    )

    records_by_date = OrderedDict()
    for c in completions:
        date_key = c.date
        if date_key not in records_by_date:
            records_by_date[date_key] = {
                'date': c.date,
                'exercises': [],
                'total_reps': 0,
                'total_calories': 0,
                'total_minutes': 0,
            }
        entry = records_by_date[date_key]
        reps = c.reps or 0
        minutes = c.exercise.duration_min or 0
        calories = (c.exercise.calories_per_set or 0) * (reps or 1) // max(1, (c.exercise.default_reps or 1))
        entry['exercises'].append({
            'name': c.exercise.name,
            'category': c.exercise.get_category_display(),
            'slug': c.exercise.slug,
            'reps': reps,
            'hold_time_sec': c.hold_time_sec,
            'notes': c.notes,
            'minutes': minutes,
            'calories': calories,
        })
        entry['total_reps'] += reps
        entry['total_calories'] += calories
        entry['total_minutes'] += minutes

    records = list(records_by_date.values())

    summary = {
        'total_sessions': completions.values('date').distinct().count(),
        'total_completions': completions.count(),
        'total_reps': sum(r['total_reps'] for r in records),
        'total_calories': sum(r['total_calories'] for r in records),
        'total_minutes': sum(r['total_minutes'] for r in records),
    }

    return render(
        request,
        'users/exercise_records.html',
        {
            'records': records,
            'summary': summary,
            'has_records': bool(records),
        },
    )


def about(request):
    return render(request, 'about.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.age = form.cleaned_data.get('age')
            profile.height_ft = form.cleaned_data.get('height_ft')
            profile.weight_kg = form.cleaned_data.get('weight_kg')
            profile.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def select_goal(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = GoalSelectionForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            profile.refresh_from_db()
            sync_goal_from_profile(request.user, profile)
            messages.success(request, 'Your goal selection has been updated.')
            return redirect('profile')
    else:
        form = GoalSelectionForm(instance=profile)

    return render(request, 'users/select_goal.html', {'form': form})
