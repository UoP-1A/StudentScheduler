from django.urls import path

from . import views


urlpatterns = [
    path("", views.get_modules, name="get-modules"),
] 