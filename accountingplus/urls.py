"""URL configuration for AccountingPlus."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

from persons.forms import AccountingAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="auth/login.html",
        authentication_form=AccountingAuthenticationForm,
        redirect_authenticated_user=True,
    ), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("persons.urls")),
]
