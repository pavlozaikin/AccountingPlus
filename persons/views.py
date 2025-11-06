from __future__ import annotations

import html
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import AccountPasswordChangeForm, PersonForm
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


RULES_FILE_PATH = Path(settings.BASE_DIR) / "data" / "militaryaccountingrules.md"
PRIMARY_COLOR = "#ffba00"
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BRACED_TEXT_PATTERN = re.compile(r"\{[^{}]*\}")


def _load_rules_html() -> str:
    raw_text = RULES_FILE_PATH.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    if not lines:
        return ""

    heading = lines[0].lstrip("# ").strip()
    subtitle = ""
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines):
        subtitle = lines[idx].strip()
        idx += 1

    body_lines = lines[idx:]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    body_text = "\n".join(body_lines)
    body_text = re.sub(r"(?m)^(\s*)\* ?", r"\1• ", body_text)
    body_html = _render_body_html(body_text)

    parts: list[str] = []
    parts.append(f"<h1>{escape(heading)}</h1>")
    if subtitle:
        parts.append(f'<p class="rules-subtitle">{escape(subtitle)}</p>')
    if body_text:
        parts.append(f'<div class="rules-plain-text">{body_html}</div>')
    return "".join(parts)


def _render_body_html(text: str) -> str:
    segments: list[str] = []
    last_index = 0
    for match in BRACED_TEXT_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_index:
            segments.append(_render_links(text[last_index:start]))

        inner = match.group(0)[1:-1]
        rendered_inner = _render_links(inner, braced=True)
        segments.append(f'<span class="rules-braced">&#123;{rendered_inner}&#125;</span>')
        last_index = end

    if last_index < len(text):
        segments.append(_render_links(text[last_index:]))
    return "".join(segments)


def _render_links(text: str, *, braced: bool = False) -> str:
    segments: list[str] = []
    last_index = 0
    for match in MARKDOWN_LINK_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_index:
            segments.append(escape(text[last_index:start]))

        label = escape(match.group(1))
        url = html.escape(match.group(2).strip(), quote=True)
        classes = ["rules-link"]
        if braced:
            classes.append("rules-link--braced")
        class_attr = " ".join(classes)
        segments.append(
            f'<a class="{class_attr}" href="{url}" target="_blank" rel="noopener noreferrer" data-label="{label}">{label}</a>'
        )
        last_index = end

    if last_index < len(text):
        segments.append(escape(text[last_index:]))

    return "".join(segments)


def _get_weasyprint_html() -> Optional[type]:
    try:
        from weasyprint import HTML as WeasyPrintHTML  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return None
    return WeasyPrintHTML


def _build_rules_context(person: Person) -> Dict[str, Any]:
    acknowledgement_note = "З Правилами військового обліку ознайомлений"
    if person.gender == "female":
        acknowledgement_note = "З Правилами військового обліку ознайомлена"

    return {
        "person": person,
        "rules_html": mark_safe(_load_rules_html()),
        "acknowledged_on": timezone.localdate(),
        "primary_color": PRIMARY_COLOR,
        "acknowledgement_note": acknowledgement_note,
    }


class PersonRulesView(LoginRequiredMixin, SidebarContextMixin, DetailView):
    model = Person
    template_name = "persons/person_rules.html"
    context_object_name = "person"
    sidebar_active = "list"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(_build_rules_context(self.object))
        return context


class PersonRulesPdfView(LoginRequiredMixin, DetailView):
    model = Person
    context_object_name = "person"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        html_renderer = _get_weasyprint_html()
        if html_renderer is None:
            return HttpResponse(
                "PDF generation is unavailable. Please install WeasyPrint.",
                status=503,
            )
        self.object = self.get_object()
        context = _build_rules_context(self.object)
        context["request"] = request
        html = render_to_string("persons/person_rules_pdf.html", context)
        pdf_bytes = html_renderer(
            string=html,
            base_url=request.build_absolute_uri("/"),
        ).write_pdf()
        filename = slugify(f"pravila-{self.object.last_name}-{self.object.first_name}") or "pravila"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response
