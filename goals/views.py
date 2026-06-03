from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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
