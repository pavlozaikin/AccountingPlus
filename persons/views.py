from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import PersonForm
from .models import Person
from .recommendations import PersonRecommendationEngine, PersonData


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
        messages.info(self.request, "Отримано рекомендації експертної системи")
        context = self.get_context_data(form=form, recommendations=recommendations)
        return self.render_to_response(context)


class PersonListView(LoginRequiredMixin, SidebarContextMixin, ListView):
    model = Person
    template_name = "persons/person_list.html"
    context_object_name = "persons"
    sidebar_active = "list"


class PersonCreateView(LoginRequiredMixin, SidebarContextMixin, RecommendationMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"
    sidebar_active = "create"
    success_url = reverse_lazy("persons:person_list")


class PersonUpdateView(LoginRequiredMixin, SidebarContextMixin, RecommendationMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"
    sidebar_active = "list"
    success_url = reverse_lazy("persons:person_list")


class PersonDeleteView(LoginRequiredMixin, SidebarContextMixin, DeleteView):
    model = Person
    template_name = "persons/person_confirm_delete.html"
    success_url = reverse_lazy("persons:person_list")
    context_object_name = "person"
    sidebar_active = "list"

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Запис успішно видалено")
        return super().delete(request, *args, **kwargs)
