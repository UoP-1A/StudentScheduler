# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_view, name='notifications'),  # View notifications
    path('mark_as_read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),  # Mark as read
]
