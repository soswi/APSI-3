from django.urls import path

from .views import csrf_view, login_view, logout_view, me_view, preferences_view, signup_view, verify_email_view

urlpatterns = [
    path('csrf', csrf_view, name='csrf'),
    path('signup', signup_view, name='signup'),
    path('verify-email', verify_email_view, name='verify-email'),
    path('login', login_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('me', me_view, name='me'),
    path('preferences', preferences_view, name='preferences'),
]
