"""URL routing for authentication application."""

from django.urls import path
from authentication.views import login_view, logout_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
