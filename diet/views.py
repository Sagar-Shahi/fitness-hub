from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import NutritionRecordForm
from .models import NutritionRecord
from .nutrition_calc import generate_nutrition_plan


@login_required
def index(request):
    records = NutritionRecord.objects.filter(user=request.user).order_by('-date')
    profile = getattr(request.user, 'profile', None)
    plan = None
    if profile:
        plan = generate_nutrition_plan(profile)
    return render(request, 'diet/index.html', {'records': records, 'plan': plan})


@login_required
def create_record(request):
    initial = {}
    profile = getattr(request.user, 'profile', None)
    if profile:
        plan = generate_nutrition_plan(profile)
        if plan.get('ready'):
            initial = {
                'date': date.today().isoformat(),
                'calories': plan['calories'],
                'protein': plan['protein'],
                'carbs': plan['carbs'],
                'fats': plan['fats'],
                'notes': plan['notes'],
            }
    if request.method == 'POST':
        form = NutritionRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            messages.success(request, 'Nutrition record saved.')
            return redirect('diet')
    else:
        form = NutritionRecordForm(initial=initial)
    return render(request, 'diet/create.html', {
        'form': form,
        'plan': generate_nutrition_plan(profile) if profile else None,
    })


@login_required
def edit_record(request, pk):
    rec = get_object_or_404(NutritionRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        form = NutritionRecordForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nutrition record updated.')
            return redirect('diet')
    else:
        form = NutritionRecordForm(instance=rec)
    return render(request, 'diet/edit.html', {'form': form, 'record': rec})


@login_required
def delete_record(request, pk):
    rec = get_object_or_404(NutritionRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        rec.delete()
        messages.success(request, 'Nutrition record deleted.')
        return redirect('diet')
    return render(request, 'diet/delete_confirm.html', {'record': rec})


@login_required
def suggest(request):
    profile = getattr(request.user, 'profile', None)
    plan = generate_nutrition_plan(profile) if profile else None
    return render(request, 'diet/suggest.html', {'plan': plan})
