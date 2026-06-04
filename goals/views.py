from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import GoalForm
from .models import Goal


@login_required
def index(request):
    goals = Goal.objects.filter(user=request.user)
    return render(request, 'goals/index.html', {'goals': goals})


@login_required
def create_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.focus_areas = form.cleaned_data.get('focus_areas', [])
            goal.save()
            return redirect('goals')
    else:
        form = GoalForm()
    return render(request, 'goals/create.html', {'form': form})


@login_required
def edit_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.focus_areas = form.cleaned_data.get('focus_areas', [])
            goal.save()
            messages.success(request, 'Goal updated successfully.')
            return redirect('goals')
    else:
        form = GoalForm(instance=goal)
    return render(request, 'goals/edit.html', {'form': form, 'goal': goal})


@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully.')
        return redirect('goals')
    return render(request, 'goals/delete_confirm.html', {'goal': goal})
