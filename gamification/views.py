"""Views for the gamification pages and JSON API.

Pages:
    - index         — Player HUD: XP, level, daily quests, recent badges.
    - badges        — Full badge catalog + which ones you've unlocked.
    - quests        — Daily + weekly quest board with claim button.
    - leaderboard   — Top XP / streak users (gated to authenticated users).

API:
    - api_summary        — JSON player summary for the chatbot to read.
    - api_award_debug    — Manual XP award (dev / testing).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from . import services as svc
from .models import Badge, Quest, UserBadge, UserQuest, XPEvent


@login_required
def index(request):
    summary = svc.get_player_summary(request.user)
    # Make sure today has daily quests.
    svc.generate_daily_quests(request.user)
    summary = svc.get_player_summary(request.user)

    all_badges = list(Badge.objects.all().order_by('tier', 'name'))
    unlocked = set(
        UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
    )
    badge_rows = [
        {
            'badge': b,
            'unlocked': b.id in unlocked,
        }
        for b in all_badges
    ]

    # Read transient announcements from session (set by other views) so the
    # modal/toast fire exactly once on this page load.
    levelup = request.session.pop('gamification_levelup', None)
    badge_toasts = request.session.pop('gamification_badges', None) or []

    return render(request, 'gamification/index.html', {
        'summary': summary,
        'badge_rows': badge_rows,
        'levelup_payload': levelup,
        'badge_toasts': badge_toasts,
    })


@login_required
def badges(request):
    all_badges = list(Badge.objects.all().order_by('tier', 'name'))
    unlocked = {
        ub.badge_id: ub
        for ub in UserBadge.objects.filter(user=request.user).select_related('badge')
    }
    badge_rows = [
        {
            'badge': b,
            'unlocked': b.id in unlocked,
            'unlocked_at': unlocked[b.id].unlocked_at if b.id in unlocked else None,
        }
        for b in all_badges
    ]
    return render(request, 'gamification/badges.html', {
        'badge_rows': badge_rows,
        'unlocked_count': len(unlocked),
        'total_count': len(all_badges),
    })


@login_required
def quests(request):
    svc.generate_daily_quests(request.user)
    daily = list(
        UserQuest.objects.filter(
            user=request.user, quest__frequency='daily',
        ).select_related('quest').order_by('-assigned_date', 'id')[:20]
    )
    weekly = list(
        UserQuest.objects.filter(
            user=request.user, quest__frequency='weekly',
        ).select_related('quest').order_by('-assigned_date', 'id')[:20]
    )
    return render(request, 'gamification/quests.html', {
        'daily': daily,
        'weekly': weekly,
    })


@login_required
@require_POST
def claim_quest_view(request, uq_id):
    uq = get_object_or_404(UserQuest, pk=uq_id, user=request.user)
    # Capture pre-claim level so we can detect a level-up caused by the reward XP.
    from .models import PlayerStats
    pre_stats, _ = PlayerStats.objects.get_or_create(user=request.user)
    pre_level = pre_stats.level

    result = svc.claim_quest(uq)
    if result.get('already_claimed'):
        messages.info(request, 'That quest was already claimed.')
    elif result.get('not_ready'):
        messages.warning(request, 'That quest is not finished yet.')
    else:
        # Detect level-up caused by the reward XP.
        pre_stats.refresh_from_db()
        new_level = pre_stats.level
        if new_level > pre_level:
            request.session['gamification_levelup'] = json.dumps({
                'level': new_level,
                'title': pre_stats.title,
                'levels_gained': new_level - pre_level,
            })

        # Always check for newly-unlocked badges after the claim.
        new_badges = svc.check_and_unlock_badges(request.user)
        if new_badges:
            request.session['gamification_badges'] = json.dumps([
                {'icon': ub.badge.icon, 'name': ub.badge.name, 'description': ub.badge.description}
                for ub in new_badges
            ])

        messages.success(
            request,
            f"Quest complete! +{result['xp']} XP" + (f" +{result['coins']} coins" if result.get('coins') else ''),
        )
    return redirect('gamification:index')


@login_required
@require_POST
def refresh_quests(request):
    """Dev-only: re-roll today's daily quests (testing)."""
    UserQuest.objects.filter(
        user=request.user, quest__frequency='daily', status='active',
    ).delete()
    svc.generate_daily_quests(request.user)
    messages.success(request, 'Quests refreshed.')
    return redirect('gamification:quests')


@login_required
def leaderboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    top_xp = list(
        User.objects.filter(player_stats__isnull=False)
        .select_related('player_stats')
        .order_by('-player_stats__xp')[:25]
    )
    top_streak = list(
        User.objects.filter(workout_stats__isnull=False)
        .select_related('workout_stats')
        .order_by('-workout_stats__current_streak', '-workout_stats__longest_streak')[:25]
    )
    my_rank_xp = None
    my_xp = svc.get_or_create_stats(request.user).xp
    if my_xp > 0:
        my_rank_xp = User.objects.filter(player_stats__xp__gt=my_xp).count() + 1
    return render(request, 'gamification/leaderboard.html', {
        'top_xp': top_xp,
        'top_streak': top_streak,
        'my_xp': my_xp,
        'my_rank_xp': my_rank_xp,
    })


@login_required
def api_summary(request):
    summary = svc.get_player_summary(request.user)
    summary['username'] = request.user.username
    summary['is_authenticated'] = True
    # Strip non-JSON-serializable fields (model instances, querysets).
    summary.pop('daily_quests', None)
    summary.pop('recent_badges', None)
    summary.pop('recent_xp', None)
    return JsonResponse(summary)


@login_required
@require_POST
def api_award_debug(request):
    """Dev / testing helper: award XP manually. Disabled unless DEBUG."""
    from django.conf import settings
    if not settings.DEBUG:
        return JsonResponse({'error': 'disabled'}, status=403)
    try:
        amount = int(request.POST.get('amount', '0'))
    except ValueError:
        amount = 0
    source = request.POST.get('source', 'other')
    description = request.POST.get('description', 'Manual award')
    result = svc.award_xp(request.user, amount, source=source, description=description)
    new_badges = svc.check_and_unlock_badges(request.user)
    return JsonResponse({
        'xp': result['stats'].xp if result['stats'] else 0,
        'level': result['new_level'],
        'title': result['new_title'],
        'leveled_up': result['leveled_up'],
        'new_badges': [ub.badge.name for ub in new_badges],
    })
