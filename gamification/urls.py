from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.index, name='index'),
    path('badges/', views.badges, name='badges'),
    path('quests/', views.quests, name='quests'),
    path('quests/<int:uq_id>/claim/', views.claim_quest_view, name='claim-quest'),
    path('quests/refresh/', views.refresh_quests, name='refresh-quests'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/summary/', views.api_summary, name='api-summary'),
    path('api/award-debug/', views.api_award_debug, name='api-award-debug'),
]
