from django.urls import path

from . import views


urlpatterns = [
    path("", views.get_modules, name="get-modules"),
    path("add-module/", views.add_module, name="add-module"),
    path("add-grade/", views.add_grade, name="add-grade"),
    path("delete-module/<int:module_id>/", views.delete_module, name="delete-module"),
    path("delete-grade/<int:grade_id>/", views.delete_grade, name="delete-grade"),
]