from __future__ import annotations

from django.urls import path

from . import views

app_name = "persons"

urlpatterns = [
    path("settings/", views.AccountSettingsView.as_view(), name="settings"),
    path("", views.PersonListView.as_view(), name="person_list"),
    path("tck-reference/", views.TckReferenceView.as_view(), name="tck_reference"),
    path("persons/create/", views.PersonCreateView.as_view(), name="person_create"),
    path("persons/<int:pk>/update/", views.PersonUpdateView.as_view(), name="person_update"),
    path("persons/<int:pk>/delete/", views.PersonDeleteView.as_view(), name="person_delete"),
    path("persons/<int:pk>/rules/", views.PersonRulesView.as_view(), name="person_rules"),
    path("persons/<int:pk>/rules/pdf/", views.PersonRulesPdfView.as_view(), name="person_rules_pdf"),
]
