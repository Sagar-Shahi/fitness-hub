# Workout Completion API Documentation

## Overview

This document describes the backend logic and database integration for recording completed exercises, tracking user progress, and generating dynamic feedback. The system automatically updates user statistics, calculates volume trends, and displays intelligent focus alignment messages.

---

## 1. Workout Completion Handler

### Function: `finish_exercise(user, exercise, reps=None, hold_time_sec=None, notes='')`

**Location**: `progress/views.py`

**Purpose**: Creates an exercise completion record and updates user workout statistics.

**Parameters**:
- `user` (User): Django User instance
- `exercise` (Exercise): Exercise instance being completed
- `reps` (int, optional): Number of repetitions completed
- `hold_time_sec` (int, optional): Hold time in seconds
- `notes` (str, optional): Additional notes about the exercise

**Returns**: ExerciseCompletion instance

**Example Usage**:
```python
from django.contrib.auth.models import User
from exercises.models import Exercise
from progress.views import finish_exercise

user = User.objects.get(username='john_doe')
exercise = Exercise.objects.get(slug='push-up')

# Record a completed exercise
completion = finish_exercise(
    user=user,
    exercise=exercise,
    reps=20,
    hold_time_sec=None,
    notes='Great form today!'
)
```

**Database Operations**:
1. Creates ExerciseCompletion record with:
   - `user_id`: User performing the exercise
   - `exercise_id`: Exercise being completed
   - `date`: Auto-set to today
   - `reps`: Repetitions (if applicable)
   - `hold_time_sec`: Hold duration (if applicable)
   - `notes`: User notes

2. Updates or creates UserWorkoutStats:
   - Increments `total_workouts` (once per day)
   - Updates `last_workout_date`
   - Calls `update_streak()` to maintain streak tracking

---

## 2. User Workout Statistics Model

### Model: `UserWorkoutStats`

**Location**: `progress/models.py`

**Purpose**: Tracks user motivation metrics and workout consistency.

**Fields**:
- `user` (OneToOneField): Link to User instance
- `total_workouts` (PositiveIntegerField): Cumulative workout count
- `current_streak` (PositiveIntegerField): Consecutive days with workouts
- `longest_streak` (PositiveIntegerField): Personal best streak
- `last_workout_date` (DateField): Date of most recent workout
- `updated_at` (DateTimeField): Auto-updated timestamp

**Key Method: `update_streak()`**

Automatically called when a new exercise is logged. Updates streak based on workout continuity:
- **Same day**: Streak continues (multiple exercises same day)
- **Next day**: Streak increments
- **2+ days gap**: Streak resets to 1

**Example Database Entry**:
```
user_id: 42
total_workouts: 156
current_streak: 12
longest_streak: 47
last_workout_date: 2024-06-03
updated_at: 2024-06-03 14:30:00
```

---

## 3. Volume Trend Calculation

### Function: `calculate_volume_trend(user, focus_area, days=7)`

**Location**: `progress/views.py`

**Purpose**: Analyzes exercise volume over time for a specific focus area.

**Parameters**:
- `user` (User): User instance
- `focus_area` (str): One of: 'upper_body', 'lower_body', 'core', 'pull_strength', 'push_strength', 'mobility'
- `days` (int): Lookback period (default 7 days)

**Returns**: Dictionary with:
```python
{
    'total_volume': 342,           # Total Sets × Reps + hold times
    'target_volume': 150,          # Focus area target
    'completion_percent': 228,     # Percentage of target
    'daily_breakdown': [           # Daily volume
        (date(2024, 5, 28), 45),
        (date(2024, 5, 29), 62),
        (date(2024, 5, 30), 58),
        ...
    ],
    'trend_direction': 'up'        # 'up', 'down', or 'stable'
}
```

**Volume Calculation**:
- For rep-based exercises: `volume = reps`
- For hold-based exercises: `volume = hold_time_sec / 30`
- Daily total: Sum of all exercises that day

**Trend Direction Logic**:
- Compare first half average vs second half average of the period
- 'up': Second half > first half by 10%+
- 'down': Second half < first half by 10%+
- 'stable': Within 10% variance

**Volume Targets by Focus Area** (per week):
```python
FOCUS_VOLUME_TARGETS = {
    'upper_body': 150,
    'lower_body': 120,
    'core': 100,
    'pull_strength': 80,
    'push_strength': 80,
    'mobility': 60,
}
```

**Example**:
```python
from progress.views import calculate_volume_trend

volume = calculate_volume_trend(user, 'upper_body', days=7)
print(f"This week: {volume['total_volume']} volume (target: {volume['target_volume']})")
print(f"Completion: {volume['completion_percent']}%")
print(f"Trend: {volume['trend_direction']}")
```

---

## 4. Weekly Completion Percentage

### Function: `calculate_weekly_completion_percent(user, goal=None)`

**Location**: `progress/views.py`

**Purpose**: Calculates how many assigned exercises were completed this week.

**Parameters**:
- `user` (User): User instance
- `goal` (Goal, optional): Goal instance (uses active goal if not provided)

**Returns**: Dictionary with:
```python
{
    'percent': 75,                    # Completion percentage
    'exercises_completed': 9,         # Unique exercises done this week
    'exercises_assigned': 12,         # Total assigned exercises
}
```

**Logic**:
- Counts unique exercises from assigned exercises list
- Looks back 7 days from today
- Calculates: `(completed / assigned) * 100`

**Example**:
```python
from progress.views import calculate_weekly_completion_percent

stats = calculate_weekly_completion_percent(user)
print(f"Weekly: {stats['exercises_completed']}/{stats['exercises_assigned']} exercises")
print(f"Progress: {stats['percent']}%")
```

---

## 5. Dynamic Focus Alignment Message

### Function: `generate_focus_alignment_message(user, goal=None)`

**Location**: `progress/views.py`

**Purpose**: Generates personalized motivational feedback based on user performance.

**Parameters**:
- `user` (User): User instance
- `goal` (Goal, optional): Goal instance

**Returns**: Dictionary with:
```python
{
    'message': 'You haven\'t hit your Upper Body target this week. Focus on Push-ups or Dips tomorrow!',
    'message_type': 'warning',  # 'alert', 'info', 'success', 'warning'
    'volume_stats': {...},      # From calculate_volume_trend
    'weekly_stats': {...},      # From calculate_weekly_completion_percent
}
```

**Message Generation Logic**:

| Completion % | Trend | Message Type | Example Message |
|---|---|---|---|
| < 50% | Any | warning | "You haven't hit your [area] target. Focus on [exercise] tomorrow!" |
| 50-99% | up | success | "Great job! Your [area] volume is up 15% this week. Keep it up!" |
| 50-99% | down | alert | "You're at 75%. Let's push harder this week!" |
| 50-99% | stable | info | "You're making steady progress. Keep going!" |
| >= 100% | up | success | "Excellent! You exceeded your target by 28%. You're crushing it!" |
| >= 100% | Any | success | "You hit your target! Maintain this consistency!" |

**Exercise Suggestions by Focus Area**:
- **upper_body**: Push-ups or Dips
- **lower_body**: Squats or Lunges
- **core**: Hollow Hold or Leg Raises
- **pull_strength**: Pull-ups or Chin-ups
- **push_strength**: Push-ups or Dips
- **mobility**: Mobility drills

**Example**:
```python
from progress.views import generate_focus_alignment_message

feedback = generate_focus_alignment_message(user)
print(f"[{feedback['message_type'].upper()}] {feedback['message']}")
print(f"Volume: {feedback['volume_stats']['completion_percent']}%")
print(f"Weekly: {feedback['weekly_stats']['percent']}%")
```

---

## 6. Database Schema

### ExerciseCompletion Table
```sql
CREATE TABLE exercises_exercisecompletion (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL (FK),
    exercise_id INTEGER NOT NULL (FK),
    date DATE NOT NULL,
    reps INTEGER,
    hold_time_sec INTEGER,
    notes TEXT
);
```

### UserWorkoutStats Table
```sql
CREATE TABLE progress_userworkoutstats (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE (FK),
    total_workouts INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_workout_date DATE,
    updated_at DATETIME AUTO_UPDATE
);
```

### Key Relationships
- `ExerciseCompletion.user_id` → `User.id` (CASCADE DELETE)
- `ExerciseCompletion.exercise_id` → `Exercise.id` (CASCADE DELETE)
- `UserWorkoutStats.user_id` → `User.id` (CASCADE DELETE)

---

## 7. Integration Points

### Progress Page View
**Location**: `progress/views.py:index()`

**Context Data Passed to Template**:
```python
{
    'completions': recent_exercises_list,
    'goal': current_goal,
    'assigned_exercises': goal_exercises,
    'focus_suggestions': suggestions_list,
    'focus_alignment': focus_message_dict,  # NEW
    'stats': user_workout_stats,             # NEW
}
```

### Dashboard View
**Location**: `dashboard/views.py:index()`

**Context Data Passed to Template**:
```python
{
    'goal': active_goal,
    'next_exercise': next_suggested,
    'readiness': goal_readiness_percent,
    'focus_alignment': focus_message_dict,  # NEW
    'stats': user_workout_stats,             # NEW
}
```

### Template Rendering
**Progress Template**: `templates/progress/index.html`
```html
{% if focus_alignment %}
  <div class="alert alert-{{ focus_alignment.message_type }}">
    <p>{{ focus_alignment.message }}</p>
    <small>Volume: {{ focus_alignment.volume_stats.completion_percent }}%</small>
  </div>
{% endif %}

{% if stats %}
  <p>Total: {{ stats.total_workouts }} | Streak: {{ stats.current_streak }}🔥</p>
{% endif %}
```

**Dashboard Template**: `templates/dashboard/index.html`
- Displays focus alignment at top
- Shows motivation stats (streak, total workouts)
- Updates weekly progress card with completion %

---

## 8. Security & Data Integrity

### Transaction Safety
- All database updates use Django ORM transactions
- UserWorkoutStats creation is idempotent (get_or_create)
- Streak updates are atomic and time-safe

### Relational Constraints
```python
# Cascade deletes ensure data consistency
class ExerciseCompletion(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    exercise = ForeignKey(Exercise, on_delete=models.CASCADE)

class UserWorkoutStats(models.Model):
    user = OneToOneField(User, on_delete=models.CASCADE)
```

### Input Validation
- `reps` and `hold_time_sec` are PositiveInteger (> 0 or NULL)
- `focus_area` choices are validated against GOAL_FOCUS_CHOICES
- Date lookback defaults to safe values (7 days)

---

## 9. Admin Interface

### UserWorkoutStats Admin
**Location**: `progress/admin.py`

**Features**:
- Display: user, total_workouts, current_streak, longest_streak, last_workout_date
- Filters: updated_at
- Read-only fields: total_workouts, current_streak, longest_streak, updated_at
- Search: user__username

**Access**: `/admin/progress/userworkoutstats/`

---

## 10. Testing the Integration

### Test Scenario 1: Log an Exercise
```python
from django.contrib.auth.models import User
from exercises.models import Exercise
from progress.views import finish_exercise

user = User.objects.get(username='testuser')
exercise = Exercise.objects.get(slug='push-up')

# Log 20 push-ups
completion = finish_exercise(user, exercise, reps=20)
print(completion)  # ExerciseCompletion(id=123, user=testuser, exercise=push-up, date=2024-06-03)

# Check stats updated
stats = user.workout_stats
print(f"Total: {stats.total_workouts}, Streak: {stats.current_streak}")
```

### Test Scenario 2: View Focus Message
```python
from progress.views import generate_focus_alignment_message

feedback = generate_focus_alignment_message(user)
print(f"Message: {feedback['message']}")
print(f"Type: {feedback['message_type']}")
print(f"Volume: {feedback['volume_stats']['completion_percent']}%")
```

### Test Scenario 3: Dashboard Display
```python
# Visit http://localhost:8000/dashboard/
# Should display:
# - Motivation stats (streak, total)
# - Focus alignment message
# - Weekly progress percentage
# - Goal readiness bar
```

---

## 11. API Endpoints (via Views)

| Endpoint | Method | Handler | Purpose |
|---|---|---|---|
| `/progress/` | GET | `index()` | Display exercise log & stats |
| `/progress/log/<slug>/` | POST | `log_exercise()` | Record exercise completion |
| `/dashboard/` | GET | `index()` | Show motivation & focus data |

---

## 12. Troubleshooting

### Issue: Stats not updating
**Solution**: Ensure `UserWorkoutStats.update_streak()` is called in `finish_exercise()`. Check that datetime timezone is correct.

### Issue: Volume calculation shows zero
**Solution**: Verify exercises have `category` matching focus_to_categories mapping. Check that completed exercises are within date range.

### Issue: Message not displaying
**Solution**: Ensure `goal` is set in user's profile. Check that `focus_alignment` dictionary is passed to template context.

### Issue: Streak resets unexpectedly
**Solution**: Check system timezone settings. Ensure `last_workout_date` is being compared with `timezone.now().date()`.

---

## 13. Performance Considerations

### Database Query Optimization
- Queries use `select_related()` and `prefetch_related()` where applicable
- Volume calculations loop through completions in memory (suitable for typical users)
- Consider pagination for users with 1000+ completions

### Caching Recommendations
- Cache `calculate_volume_trend()` for 1 hour per user
- Cache `generate_focus_alignment_message()` for 2 hours
- Invalidate on new exercise completion

**Example Cache Implementation**:
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 2)  # 2 hours
def index(request):
    # ... view logic
```

---

## Summary

The workout completion system provides:
1. **Automatic tracking** of exercise completions
2. **Motivation metrics** via streaks and workout counts
3. **Volume analysis** by focus area with trend detection
4. **Personalized feedback** based on performance
5. **Secure data storage** with relational integrity
6. **Dashboard integration** for at-a-glance progress

All components work together to keep users motivated and focused on their fitness goals.
