# Workout Completion Backend - Usage Examples

This file provides practical code examples for using the workout completion and progress tracking system.

---

## Example 1: User Completes an Exercise

### Scenario
User John logs a push-up exercise from the progress page.

### Code Flow

#### 1. User POSTs to `log_exercise` view
```python
# In templates/progress/log_exercise.html
<form method="POST" action="{% url 'log-exercise' exercise.slug %}">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-success">Log Exercise</button>
</form>
```

#### 2. View handles the submission
```python
# In progress/views.py::log_exercise()
@login_required
def log_exercise(request, slug):
    exercise = get_object_or_404(Exercise, slug=slug)
    if request.method == 'POST':
        form = ExerciseCompletionForm(request.POST)
        if form.is_valid():
            reps = form.cleaned_data.get('reps')
            hold_time_sec = form.cleaned_data.get('hold_time_sec')
            notes = form.cleaned_data.get('notes', '')
            
            # Use finish_exercise handler
            completion = finish_exercise(
                user=request.user,
                exercise=exercise,
                reps=reps,
                hold_time_sec=hold_time_sec,
                notes=notes
            )
            return redirect('exercise-detail', slug=slug)
```

#### 3. finish_exercise() creates record and updates stats
```python
def finish_exercise(user, exercise, reps=None, hold_time_sec=None, notes=''):
    # Create completion record
    completion = ExerciseCompletion.objects.create(
        user=user,
        exercise=exercise,
        reps=reps,
        hold_time_sec=hold_time_sec,
        notes=notes,
    )
    
    # Get or create workout stats
    stats, created = UserWorkoutStats.objects.get_or_create(user=user)
    today = timezone.now().date()
    
    # Update stats
    if not stats.last_workout_date or stats.last_workout_date != today:
        stats.total_workouts += 1
        stats.last_workout_date = today
        stats.update_streak()
    
    return completion
```

#### 4. Database State After
```
ExerciseCompletion:
  id: 1
  user_id: 5
  exercise_id: 12
  date: 2024-06-03
  reps: 20
  hold_time_sec: null
  notes: "Great form!"

UserWorkoutStats:
  id: 5
  user_id: 5
  total_workouts: 1
  current_streak: 1
  longest_streak: 1
  last_workout_date: 2024-06-03
```

---

## Example 2: User Views Progress Page

### Scenario
User navigates to `/progress/` to see their exercise log and get motivational feedback.

### Code Flow

#### 1. User requests `/progress/`
```python
# URL: /progress/
# View: progress/views.py::index()
```

#### 2. View collects all required data
```python
@login_required
def index(request):
    # Get current goal
    goal = get_current_goal(request)
    
    # Get recent exercise log
    completions = ExerciseCompletion.objects.filter(
        user=request.user
    ).order_by('-date')[:50]
    
    # Get assigned exercises for goal
    assigned_exercises = goal.assigned_exercises.all() if goal else []
    
    # Generate focus suggestions
    focus_suggestions = build_focus_suggestions(goal, completions)
    
    # Generate dynamic focus message
    focus_alignment = generate_focus_alignment_message(request.user, goal)
    
    # Get user stats
    stats = getattr(request.user, 'workout_stats', None)
    
    context = {
        'completions': completions,
        'goal': goal,
        'assigned_exercises': assigned_exercises,
        'focus_suggestions': focus_suggestions,
        'focus_alignment': focus_alignment,
        'stats': stats,
    }
    
    return render(request, 'progress/index.html', context)
```

#### 3. Template Renders with Dynamic Content
```html
<!-- templates/progress/index.html -->

<!-- User Stats -->
{% if stats %}
<div class="alert alert-success mb-3">
    <h5>Your Stats</h5>
    <p>
        <strong>Total Workouts:</strong> {{ stats.total_workouts }} | 
        <strong>Current Streak:</strong> {{ stats.current_streak }} days | 
        <strong>Longest Streak:</strong> {{ stats.longest_streak }} days
    </p>
</div>
{% endif %}

<!-- Focus Alignment Message -->
{% if focus_alignment %}
<div class="alert alert-{{ focus_alignment.message_type }} mb-3">
    <h5>{{ focus_alignment.message_type|title }} Message</h5>
    <p>{{ focus_alignment.message }}</p>
    <small>
        Weekly Volume: {{ focus_alignment.volume_stats.total_volume }}/
        {{ focus_alignment.volume_stats.target_volume }} 
        ({{ focus_alignment.volume_stats.completion_percent }}%)
    </small>
</div>
{% endif %}
```

#### 4. Example Output
```
Your Stats
Total Workouts: 156 | Current Streak: 12 days | Longest Streak: 47 days

WARNING Message
You haven't hit your Upper Body target this week. Focus on Push-ups or Dips tomorrow!

Weekly Volume: 75/150 (50%) • Trend: down
```

---

## Example 3: Dashboard Shows Focus Alignment

### Scenario
User opens dashboard to see at-a-glance progress toward their goal.

### Code Flow

#### 1. Dashboard View Computes All Metrics
```python
@login_required
def index(request):
    goal = get_active_goal(request)
    readiness = compute_goal_readiness(goal, request.user)
    
    # NEW: Get focus alignment
    focus_alignment = get_focus_alignment_message(request)
    
    # NEW: Get stats
    stats = getattr(request.user, 'workout_stats', None)
    
    context = {
        'goal': goal,
        'readiness': readiness,
        'focus_alignment': focus_alignment,
        'stats': stats,
    }
    
    return render(request, 'dashboard/index.html', context)
```

#### 2. calculate_volume_trend() Analyzes 7-Day Performance
```python
def calculate_volume_trend(user, focus_area, days=7):
    # Query exercises from last 7 days
    start_date = timezone.now().date() - timedelta(days=days)
    completions = ExerciseCompletion.objects.filter(
        user=user,
        exercise__category__in=['chest', 'back', 'shoulders'],  # upper_body
        date__gte=start_date,
    )
    
    # Calculate volume (Sets × Reps)
    total_volume = sum(comp.reps or 1 for comp in completions)
    
    # Determine trend
    # Compare first 3 days avg vs last 3 days avg
    
    return {
        'total_volume': 120,
        'target_volume': 150,
        'completion_percent': 80,
        'trend_direction': 'up',
        'daily_breakdown': [
            (date(2024, 5, 28), 15),
            (date(2024, 5, 29), 20),
            (date(2024, 5, 30), 22),
        ]
    }
```

#### 3. Dashboard Template Displays Message
```html
<div class="alert alert-success mb-4">
    <h5>Success — Focus on Your Goal</h5>
    <p>Great job! Your Upper Body volume is up 15% this week. Keep it up!</p>
    <small>Weekly Volume: 120/150 (80%) • Trend: Up</small>
</div>

<div class="alert alert-info mb-4">
    <h5>Your Motivation Stats</h5>
    <p>
        <strong>Total Workouts:</strong> 156 | 
        <strong>Current Streak:</strong> 12 🔥 | 
        <strong>Longest Streak:</strong> 47 days
    </p>
</div>
```

---

## Example 4: Calculating Weekly Completion Percentage

### Scenario
System needs to show user progress toward their weekly goal.

### Code Flow

```python
from progress.views import calculate_weekly_completion_percent
from exercises.models import ExerciseCompletion
from goals.models import Goal

# Get user's goal (e.g., Calisthenics Body)
goal = Goal.objects.get(user=user, goal_type='calisthenics')

# Get assigned exercises (e.g., 12 exercises for calisthenics)
assigned = goal.assigned_exercises.all()  # 12 exercises

# Query completions from last 7 days
start_date = timezone.now().date() - timedelta(days=7)
completions = ExerciseCompletion.objects.filter(
    user=user,
    exercise__in=assigned,
    date__gte=start_date,
)

# Count unique exercises completed
completed_unique = completions.values('exercise').distinct().count()
# Result: 9 exercises completed

# Calculate percentage
percent = (9 / 12) * 100  # 75%

# Return
{
    'percent': 75,
    'exercises_completed': 9,
    'exercises_assigned': 12,
}
```

### Template Output
```html
<div class="progress">
    <div class="progress-bar" style="width: 75%;"></div>
</div>
<p>9/12 exercises completed (75%)</p>
```

---

## Example 5: Dynamic Message Generation

### Scenario
System generates different messages based on user's volume completion percentage.

### Condition 1: Low Volume (< 50%)
```python
completion_percent = 35
trend = 'down'

message = "You haven't hit your Upper Body target this week. Focus on Push-ups or Dips tomorrow!"
message_type = 'warning'
```

### Condition 2: Good Progress (50-99%, Trending Up)
```python
completion_percent = 80
trend = 'up'

message = "Great job! Your Upper Body volume is up 15% this week. Keep it up!"
message_type = 'success'
```

### Condition 3: Exceeding Target (>= 100%)
```python
completion_percent = 125
trend = 'up'

message = "Excellent! You exceeded your Upper Body target by 25%. You're crushing it!"
message_type = 'success'
```

### Condition 4: Stagnant Progress (50-99%, Stable Trend)
```python
completion_percent = 70
trend = 'stable'

message = "You're making steady progress on your Upper Body goal. Keep going!"
message_type = 'info'
```

---

## Example 6: Admin Interface Usage

### Access User Stats
```
1. Navigate to /admin/progress/userworkoutstats/
2. Click on a user's stats entry
3. View read-only fields:
   - Total Workouts: 156
   - Current Streak: 12 days
   - Longest Streak: 47 days
   - Last Workout Date: 2024-06-03
   - Updated At: 2024-06-03 14:30:00 UTC
```

### Monitor Exercise Completions
```
1. Navigate to /admin/exercises/exercisecompletion/
2. Filter by:
   - Date range (e.g., last 7 days)
   - User (specific user)
   - Exercise (specific exercise)
3. View all logged exercises with:
   - User name
   - Exercise name
   - Date
   - Reps
   - Hold time
```

---

## Example 7: Streak Calculation Logic

### Scenario: User Logs Exercises Over Multiple Days

#### Day 1 (May 28, Monday)
```python
# First log of the day
stats.last_workout_date = date(2024, 5, 28)
stats.total_workouts = 1
stats.update_streak()  # days_since_last = 0, streak = 1

# Result
stats.current_streak = 1
stats.longest_streak = 1
```

#### Day 2 (May 29, Tuesday)
```python
# Log second day
stats.last_workout_date = date(2024, 5, 29)
stats.total_workouts = 2
stats.update_streak()  # days_since_last = 1, streak = 2

# Result
stats.current_streak = 2
stats.longest_streak = 2
```

#### Day 3 (May 29, Same Day)
```python
# Another log same day (doesn't break streak)
stats.last_workout_date = date(2024, 5, 29)  # unchanged
stats.total_workouts = 2  # unchanged
stats.save()

# Result (streak continues)
stats.current_streak = 2
```

#### Day 4 (May 31, Thursday - Gap Day)
```python
# Missed May 30 (gap of 2 days)
stats.last_workout_date = date(2024, 5, 31)
stats.total_workouts = 3
stats.update_streak()  # days_since_last = 2, streak resets to 1

# Result
stats.current_streak = 1
stats.longest_streak = 2  # unchanged
```

---

## Example 8: Error Handling

### Scenario 1: User Hasn't Set a Goal
```python
# In generate_focus_alignment_message()
if not goal:
    return {
        'message': 'Set up a goal to get personalized feedback!',
        'message_type': 'info',
        'volume_stats': {},
        'weekly_stats': {},
    }
```

### Scenario 2: No Exercises Logged Yet
```python
# In calculate_volume_trend()
completions = ExerciseCompletion.objects.filter(
    user=user,
    exercise__category__in=categories,
    date__gte=start_date,
)  # Returns empty queryset

total_volume = 0  # Default
completion_percent = 0
trend_direction = 'stable'  # Default
```

### Scenario 3: Missing UserWorkoutStats
```python
# In progress/views.py::index()
stats = getattr(request.user, 'workout_stats', None)
# Returns None if not created yet
# Template handles with {% if stats %}
```

---

## Example 9: Database Query Performance

### Optimized Query for Volume Trend
```python
# GOOD: Single query with filter
start_date = timezone.now().date() - timedelta(days=7)
completions = ExerciseCompletion.objects.filter(
    user=user,
    exercise__category__in=['chest', 'back'],
    date__gte=start_date,
).select_related('exercise')  # Avoid N+1

# Loop through results (already loaded)
for comp in completions:
    volume += comp.reps or 1
```

### Optimized Query for Weekly Completion
```python
# GOOD: Count distinct exercises
from django.db.models import Count

completed = ExerciseCompletion.objects.filter(
    user=user,
    exercise__in=assigned,
    date__gte=start_date,
).values('exercise').distinct().count()
```

---

## Example 10: Testing the System

### Test Script
```python
# In Django shell: python manage.py shell

from django.contrib.auth.models import User
from django.utils import timezone
from exercises.models import Exercise, ExerciseCompletion
from goals.models import Goal
from progress.views import finish_exercise, generate_focus_alignment_message

# Setup
user = User.objects.get(username='testuser')
exercise = Exercise.objects.get(slug='push-up')

# Test 1: Log an exercise
print("=== Test 1: Logging Exercise ===")
completion = finish_exercise(user, exercise, reps=20, notes='Great form')
print(f"Created: {completion}")
print(f"User Stats: {user.workout_stats}")

# Test 2: Log multiple exercises same day
print("\n=== Test 2: Multiple Exercises (Same Day) ===")
exercise2 = Exercise.objects.get(slug='pull-up')
finish_exercise(user, exercise2, reps=10)
print(f"Total Workouts: {user.workout_stats.total_workouts}")  # Still 1

# Test 3: View progress message
print("\n=== Test 3: Focus Alignment Message ===")
feedback = generate_focus_alignment_message(user)
print(f"Message: {feedback['message']}")
print(f"Type: {feedback['message_type']}")

# Test 4: View daily volume
print("\n=== Test 4: Daily Volume ===")
for date, volume in feedback['volume_stats']['daily_breakdown']:
    print(f"{date}: {volume} volume")
```

### Expected Output
```
=== Test 1: Logging Exercise ===
Created: testuser — push-up — 2024-06-03
User Stats: testuser — Total: 1, Streak: 1

=== Test 2: Multiple Exercises (Same Day) ===
Total Workouts: 1

=== Test 3: Focus Alignment Message ===
Message: You haven't hit your Upper Body target this week. Focus on Push-ups or Dips tomorrow!
Type: warning

=== Test 4: Daily Volume ===
2024-06-03: 30 volume
```

---

## Summary

The workout completion system enables:
1. **Automatic logging** via `finish_exercise()` handler
2. **Streak tracking** with intelligent gap detection
3. **Volume analysis** with trend identification
4. **Personalized feedback** based on performance data
5. **Dashboard integration** showing all metrics at a glance

All operations are transaction-safe and follow Django best practices.
