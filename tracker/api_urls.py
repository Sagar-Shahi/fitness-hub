from django.urls import path
from rest_framework.routers import SimpleRouter

from . import api

router = SimpleRouter()
router.register('workouts', api.WorkoutViewSet, basename='workout')
router.register('meals', api.MealViewSet, basename='meal')
router.register('weight', api.WeightViewSet, basename='weight')

urlpatterns = [path('summary/', api.SummaryView.as_view(), name='summary'), *router.urls]
