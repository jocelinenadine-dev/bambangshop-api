"""Authentication views for user session login and logout."""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    """Handle user login form for session authentication."""
    next_url = request.GET.get('next') or request.POST.get('next') or '/'

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'authentication/login.html', {'next': next_url})


def logout_view(request):
    """Handle user logout."""
    next_url = request.GET.get('next') or '/'
    logout(request)
    return redirect(next_url)
