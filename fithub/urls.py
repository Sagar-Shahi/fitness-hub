from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core import views as core_views

handler404 = 'core.views.error_404'
handler403 = 'core.views.error_403'
handler400 = 'core.views.error_400'
handler500 = 'core.views.error_500'

urlpatterns = [
    path('', core_views.home, name='home'),
    path('healthz/', core_views.health, name='health'),
    path('accounts/', include('accounts.urls')),
    path('api/v1/', include('tracker.api_urls')),
    path('', include('tracker.urls')),
    path('', include('shop.urls')),
    path(settings.ADMIN_URL, admin.site.urls),
]
