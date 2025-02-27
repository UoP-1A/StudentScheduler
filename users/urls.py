from django.urls import path

from users import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/delete-account-confirm", views.delete_account_confirmation_view, name="delete_account_confirmation"),
    path("profile/delete-account", views.delete_account, name="delete_account"),

    path('users/', views.user_list, name='user_list'),
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('friends/', views.friends_list, name='friends_list'),
    path('send-request/<int:user_id>/', views.send_friend_request, name='send_request'),
    path('respond-request/<int:request_id>/<str:action>/', 
         views.respond_request, 
         name='respond_request'),
]