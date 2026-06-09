"""Context processor that injects a compact player summary into every
template that has access to RequestContext. The nav XP bar uses this."""

from . import services as svc


def player_summary(request):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return {'player_summary': {}}
    return {'player_summary': svc.get_player_summary(user)}
