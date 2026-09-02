from django.urls import path
from .views import SignInView, SignOutView, SignUpView, ProfileView

urlpatterns = [
    path('sign-in', SignInView.as_view(), name='sign-in'),
    path('sign-out', SignOutView.as_view(), name='sign-out'),
    path('sign-up', SignUpView.as_view(), name='sign-up'),

    path('profile', ProfileView.as_view(), name='profile'),
]
