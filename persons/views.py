from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.contrib.auth.views import PasswordChangeView

from .forms import PersonForm, AccountPasswordChangeForm
from .models import Person
from .recommendations import PersonRecommendationEngine, PersonData
from .tck_reference_data import count_tck_entries, get_tck_reference_data


class SidebarContextMixin:
    """Provide a helper for marking the active sidebar entry."""

    sidebar_active: str = ""

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("sidebar_active", self.sidebar_active)
        return context


class RecommendationMixin:
    """Shared logic for handling recommendation requests from the form."""

    def form_valid(self, form: PersonForm) -> HttpResponse:
        action = self.request.POST.get("submit_action", "save")
        if action == "recommend":
            return self.form_recommend(form)
        messages.success(self.request, "Запис успішно збережено")
        return super().form_valid(form)

    def form_recommend(self, form: PersonForm) -> HttpResponse:
        data = form.cleaned_data
        engine = PersonRecommendationEngine()
        engine.reset()
        engine.declare(PersonData(**{k: v for k, v in data.items() if v not in (None, "")}))
        engine.run()
        recommendations = engine.get_recommendations()
        if not recommendations:
            recommendations = [
                "Додаткові рекомендації відсутні на основі введених даних."
            ]
        context = self.get_context_data(form=form, recommendations=recommendations)
        return self.render_to_response(context)


class PersonListView(LoginRequiredMixin, SidebarContextMixin, ListView):
    model = Person
    template_name = "persons/person_list.html"
    context_object_name = "persons"
    sidebar_active = "list"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if not query:
            return queryset

        terms = query.split()
        for term in terms:
            queryset = queryset.filter(
                Q(last_name__icontains=term)
                | Q(first_name__icontains=term)
                | Q(middle_name__icontains=term)
                | Q(edrpvr_number__icontains=term)
            )
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        query_string = query_params.urlencode()
        context["query_string"] = query_string
        context["pagination_query"] = f"{query_string}&" if query_string else ""
        return context


class TckReferenceView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "persons/tck_reference.html"
    sidebar_active = "tck_reference"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        reference_data = get_tck_reference_data()
        context["tck_regions"] = reference_data
        context["tck_entries_total"] = count_tck_entries(reference_data)
        return context


class PersonCreateView(LoginRequiredMixin, SidebarContextMixin, RecommendationMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"
    sidebar_active = "create"

    def get_success_url(self) -> str:
        return reverse("persons:person_update", kwargs={"pk": self.object.pk})


class PersonUpdateView(LoginRequiredMixin, SidebarContextMixin, RecommendationMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"
    sidebar_active = "list"

    def get_success_url(self) -> str:
        return reverse("persons:person_update", kwargs={"pk": self.object.pk})


class PersonDeleteView(LoginRequiredMixin, SidebarContextMixin, DeleteView):
    model = Person
    template_name = "persons/person_confirm_delete.html"
    success_url = reverse_lazy("persons:person_list")
    context_object_name = "person"
    sidebar_active = "list"

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Запис успішно видалено")
        return super().delete(request, *args, **kwargs)


class AccountSettingsView(LoginRequiredMixin, SidebarContextMixin, PasswordChangeView):
    template_name = "persons/settings.html"
    form_class = AccountPasswordChangeForm
    success_url = reverse_lazy("persons:settings")

    def form_valid(self, form: AccountPasswordChangeForm) -> HttpResponse:
        messages.success(self.request, "Пароль успішно змінено")
        return super().form_valid(form)
