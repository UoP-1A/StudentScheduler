from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark_as_read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
]