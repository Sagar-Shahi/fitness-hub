from django.urls import path

from . import views

urlpatterns = [
    path('', views.inspiration_feed, name='inspiration-feed'),
    path('icons/', views.icon_list, name='inspiration-icons'),
    path('icons/<slug:slug>/', views.icon_detail, name='inspiration-icon-detail'),
    path('quotes/', views.quote_wall, name='inspiration-quotes'),
    path('api/random-quote/', views.random_quote_api, name='inspiration-random-quote'),
]
