"""Numbers and chart geometry for the dashboard. Charts are drawn as SVG on the server, so no script is needed."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from .models import BodyMetric, Meal, Workout


def nice_ceiling(value):
    """Round up to a tidy axis maximum: 4, 5, 10, 20, 50, 100, 200 ..."""
    if value <= 4:
        return 4
    magnitude = 1
    while magnitude * 10 < value:
        magnitude *= 10
    for step in (1, 2, 5, 10):
        if step * magnitude >= value:
            return step * magnitude
    return 10 * magnitude  # pragma: no cover


def _fmt(number):
    return f'{number:.1f}'.rstrip('0').rstrip('.')


def week_start(day):
    return day - timedelta(days=day.weekday())  # Monday


def day_range(days, end=None):
    end = end or timezone.localdate()
    return [end - timedelta(days=n) for n in range(days - 1, -1, -1)]


def workouts_per_day(user, days):
    window = day_range(days)
    counts = dict(Workout.objects.filter(owner=user, date__gte=window[0], date__lte=window[-1])
                  .values_list('date').annotate(n=Count('id')))
    return [(d, counts.get(d, 0)) for d in window]


def calories_per_day(user, days):
    window = day_range(days)
    totals = dict(Meal.objects.filter(owner=user, date__gte=window[0], date__lte=window[-1])
                  .values_list('date').annotate(n=Sum('calories')))
    return [(d, totals.get(d, 0)) for d in window]


def day_totals(user, day):
    agg = Meal.objects.filter(owner=user, date=day).aggregate(
        calories=Sum('calories'), protein=Sum('protein_g'), carbs=Sum('carbs_g'), fat=Sum('fat_g'))
    return {k: v or 0 for k, v in agg.items()}


def streak(user):
    """Days in a row with a workout, counting back from today (or yesterday, if today has none yet)."""
    dates = set(Workout.objects.filter(owner=user, date__gte=timezone.localdate() - timedelta(days=400))
                .values_list('date', flat=True))
    day = timezone.localdate()
    if day not in dates:
        day -= timedelta(days=1)
    count = 0
    while day in dates:
        count += 1
        day -= timedelta(days=1)
    return count


def weight_points(user, days):
    start = timezone.localdate() - timedelta(days=days - 1)
    return [(m.date, m.weight_kg) for m in BodyMetric.objects.filter(owner=user, date__gte=start).order_by('date')]


def dashboard(user, profile):
    today = timezone.localdate()
    start = week_start(today)
    week_workouts = Workout.objects.filter(owner=user, date__gte=start, date__lte=today)
    totals = day_totals(user, today)
    latest = BodyMetric.objects.filter(owner=user).first()
    first_in_window = BodyMetric.objects.filter(owner=user, date__gte=today - timedelta(days=29)).order_by('date').first()
    change = None
    if latest and first_in_window and first_in_window.pk != latest.pk:
        change = latest.weight_kg - first_in_window.weight_kg
    return {
        'week_done': week_workouts.count(),
        'week_target': profile.weekly_workout_target,
        'week_minutes': week_workouts.aggregate(m=Sum('duration_min'))['m'] or 0,
        'today': totals,
        'calorie_target': profile.calorie_target,
        'calorie_left': profile.calorie_target - totals['calories'],
        'streak': streak(user),
        'latest_weight': latest,
        'weight_change': change,
        'target_weight': profile.target_weight_kg,
    }


def percent(done, target):
    if not target:
        return 0
    return max(0, min(100, round(100 * done / target)))


def bar_chart(series, unit, width=720, height=200):
    """Bar chart geometry. `series` is a list of (date, number). All numbers come back as printable strings."""
    left, right, top, bottom = 44, 8, 10, 26
    plot_w, plot_h = width - left - right, height - top - bottom
    days = len(series)
    peak = max((n for _, n in series), default=0)
    axis_max = nice_ceiling(peak)
    slot = plot_w / days if days else plot_w
    bar_w = max(slot * 0.68, 1.5)
    bars = []
    for index, (day, n) in enumerate(series):
        h = plot_h * n / axis_max
        bars.append({'x': _fmt(left + index * slot + (slot - bar_w) / 2), 'y': _fmt(top + plot_h - h),
                     'w': _fmt(bar_w), 'h': _fmt(h), 'n': n, 'label': f'{day:%b} {day.day}'})
    ticks = [{'value': _fmt(axis_max * f), 'y': _fmt(top + plot_h - plot_h * f)} for f in (0, 0.5, 1)]
    x_labels = []
    if days:
        for index in sorted({0, days // 2, days - 1}):
            day = series[index][0]
            x_labels.append({'text': f'{day:%b} {day.day}', 'x': _fmt(left + index * slot + slot / 2), 'y': _fmt(height - 8)})
    total = sum(n for _, n in series)
    return {'kind': 'bar', 'width': width, 'height': height, 'left': left, 'right_edge': width - right, 'bars': bars,
            'ticks': ticks, 'x_labels': x_labels, 'axis_max': axis_max, 'total': total, 'unit': unit,
            'description': f'{total} {unit} over the last {days} days, highest day {peak}.'}


def line_chart(points, unit='kg', width=720, height=200, target=None):
    """Line chart geometry for weight over time. `points` is a list of (date, Decimal) in date order."""
    left, right, top, bottom = 44, 12, 12, 26
    plot_w, plot_h = width - left - right, height - top - bottom
    if not points:
        return {'kind': 'line', 'empty': True, 'width': width, 'height': height}
    values = [float(v) for _, v in points] + ([float(target)] if target else [])
    low, high = min(values), max(values)
    pad = max((high - low) * 0.15, 1.0)
    low, high = low - pad, high + pad
    first, last = points[0][0], points[-1][0]
    span = max((last - first).days, 1)

    def x_of(day):
        return left + plot_w * ((day - first).days / span if len(points) > 1 else 0.5)

    def y_of(v):
        return top + plot_h - plot_h * (float(v) - low) / (high - low)

    dots = [{'x': _fmt(x_of(d)), 'y': _fmt(y_of(v)), 'label': f'{d:%b} {d.day}: {v} {unit}'} for d, v in points]
    path = ' '.join(f"{'M' if i == 0 else 'L'}{dot['x']} {dot['y']}" for i, dot in enumerate(dots))
    ticks = [{'value': _fmt(low + (high - low) * f), 'y': _fmt(top + plot_h - plot_h * f)} for f in (0, 0.5, 1)]
    x_labels = [{'text': f'{first:%b} {first.day}', 'x': _fmt(left), 'y': _fmt(height - 8), 'anchor': 'start'}]
    if len(points) > 1:
        x_labels.append({'text': f'{last:%b} {last.day}', 'x': _fmt(left + plot_w), 'y': _fmt(height - 8), 'anchor': 'end'})
    return {'kind': 'line', 'empty': False, 'width': width, 'height': height, 'left': left, 'right_edge': width - right,
            'dots': dots, 'path': path, 'ticks': ticks, 'x_labels': x_labels,
            'target_y': _fmt(y_of(target)) if target else None,
            'description': f'Weight from {points[0][1]} to {points[-1][1]} {unit} between {first:%b} {first.day} and {last:%b} {last.day}.'}
