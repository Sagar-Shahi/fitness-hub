from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='diet'),
    path('create/', views.create_record, name='create-record'),
    path('edit/<int:pk>/', views.edit_record, name='edit-record'),
    path('delete/<int:pk>/', views.delete_record, name='delete-record'),
]
