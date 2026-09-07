from django.urls import path
from .views import SignInView, SignOutView, SignUpView, ProfileView, AvatarUpdateView, PasswordUpdateView

urlpatterns = [
    path('sign-in', SignInView.as_view(), name='sign-in'),
    path('sign-out', SignOutView.as_view(), name='sign-out'),
    path('sign-up', SignUpView.as_view(), name='sign-up'),
    path('profile', ProfileView.as_view(), name='profile'),

    path('profile/avatar', AvatarUpdateView.as_view(), name='profile-avatar'),
    path('profile/password', PasswordUpdateView.as_view(), name='profile-password'),
]

