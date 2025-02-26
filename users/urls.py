from django.urls import path

from users import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/delete-account-confirm", views.delete_account_confirmation_view, name="delete_account_confirmation"),
    path("profile/delete-account", views.delete_account, name="delete_account"),
]