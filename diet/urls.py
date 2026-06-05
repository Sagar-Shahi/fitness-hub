from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='diet'),
    path('create/', views.create_record, name='create-record'),
    path('suggest/', views.suggest, name='diet-suggest'),
    path('edit/<int:pk>/', views.edit_record, name='edit-record'),
    path('delete/<int:pk>/', views.delete_record, name='delete-record'),
    path('foods/', views.foods, name='diet-foods'),
    path('budget-meals/', views.budget_meals, name='diet-budget-meals'),
]
