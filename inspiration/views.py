import json
import random

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import FitnessIcon, InspirationCategory, MotivationQuote


def inspiration_feed(request):
    """The main inspiration hub: category overview + featured icons + daily quote."""
    categories = InspirationCategory.objects.all().prefetch_related('icons')
    featured_icons = FitnessIcon.objects.filter(is_featured=True).select_related('category')[:6]
    daily_quote = _pick_daily_quote()
    recent_quotes = MotivationQuote.objects.filter(is_featured=True).select_related('icon', 'category')[:6]

    context = {
        'categories': categories,
        'featured_icons': featured_icons,
        'daily_quote': daily_quote,
        'recent_quotes': recent_quotes,
        'total_icons': FitnessIcon.objects.count(),
        'total_quotes': MotivationQuote.objects.count(),
    }
    return render(request, 'inspiration/inspiration_feed.html', context)


def icon_list(request):
    """Browse all fitness icons, optionally filtered by category."""
    category_slug = request.GET.get('category')
    icons = FitnessIcon.objects.select_related('category').all()
    active_category = None
    if category_slug:
        active_category = get_object_or_404(InspirationCategory, slug=category_slug)
        icons = icons.filter(category=active_category)

    categories = InspirationCategory.objects.all()
    context = {
        'icons': icons,
        'categories': categories,
        'active_category': active_category,
    }
    return render(request, 'inspiration/icon_list.html', context)


def icon_detail(request, slug):
    """Full bio + achievements + training tips + video for a single icon."""
    icon = get_object_or_404(FitnessIcon, slug=slug)
    related_icons = (
        FitnessIcon.objects
        .filter(category=icon.category)
        .exclude(pk=icon.pk)
        .select_related('category')[:3]
    )
    icon_quotes = icon.quotes.all()[:4]

    context = {
        'icon': icon,
        'related_icons': related_icons,
        'icon_quotes': icon_quotes,
    }
    return render(request, 'inspiration/icon_detail.html', context)


def quote_wall(request):
    """Browse all motivation quotes, with optional category filter."""
    category_slug = request.GET.get('category')
    quotes = MotivationQuote.objects.select_related('icon', 'category').all()
    active_category = None
    if category_slug:
        active_category = get_object_or_404(InspirationCategory, slug=category_slug)
        quotes = quotes.filter(category=active_category)

    categories = InspirationCategory.objects.all()
    context = {
        'quotes': quotes,
        'categories': categories,
        'active_category': active_category,
    }
    return render(request, 'inspiration/quote_wall.html', context)


def random_quote_api(request):
    """Return a random quote (or a specific icon's quote) as JSON for AJAX widgets."""
    icon_slug = request.GET.get('icon')
    qs = MotivationQuote.objects.all()
    if icon_slug:
        qs = qs.filter(icon__slug=icon_slug)
    if not qs.exists():
        return JsonResponse({'error': 'no_quotes'}, status=404)
    quote = random.choice(list(qs))
    return JsonResponse({
        'text': quote.text,
        'author': quote.author,
        'icon_slug': quote.icon.slug if quote.icon else '',
        'icon_name': quote.icon.name if quote.icon else '',
    })


def _pick_daily_quote():
    """Deterministically pick a quote for 'today' so the daily quote stays stable all day."""
    from django.utils import timezone
    qs = list(MotivationQuote.objects.filter(is_featured=True).values_list('id', flat=True))
    if not qs:
        qs = list(MotivationQuote.objects.all().values_list('id', flat=True))
    if not qs:
        return None
    today = timezone.now().date()
    seed = today.toordinal()
    chosen_id = qs[seed % len(qs)]
    return MotivationQuote.objects.select_related('icon', 'category').get(pk=chosen_id)
