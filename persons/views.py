from __future__ import annotations

import html
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import AccountPasswordChangeForm, PersonForm, RulesAcknowledgementSelectionForm
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


def _build_rules_bulk_context(persons: Sequence[Person]) -> Dict[str, Any]:
    persons_list = list(persons)
    acknowledgement_note = "З Правилами військового обліку ознайомлені"
    if len(persons_list) == 1:
        single_context = _build_rules_context(persons_list[0])
        acknowledgement_note = single_context["acknowledgement_note"]
    acknowledged_on = timezone.localdate()
    acknowledgement_entries = [
        {
            "date": acknowledged_on,
            "first_name": person.first_name.strip(),
            "last_name_upper": person.last_name.strip().upper(),
            "full_name": " ".join(
                value
                for value in (
                    person.first_name.strip(),
                    person.last_name.strip().upper(),
                )
                if value
            ),
        }
        for person in persons_list
    ]
    return {
        "rules_html": mark_safe(_load_rules_html()),
        "acknowledged_on": acknowledged_on,
        "acknowledgement_note": acknowledgement_note,
        "acknowledgement_entries": acknowledgement_entries,
        "selected_count": len(persons_list),
        "primary_color": PRIMARY_COLOR,
        "selected_persons": persons_list,
        "selected_person_ids": [person.pk for person in persons_list],
    }


def _serialize_person_for_recommendations(person: Person) -> Dict[str, Any]:
    payload = model_to_dict(person, fields=PersonForm.Meta.fields)  # type: ignore[arg-type]
    return {key: value for key, value in payload.items() if value not in (None, "", [])}


def _build_person_recommendations(person: Person) -> List[str]:
    engine = PersonRecommendationEngine()
    engine.reset()
    engine.declare(PersonData(**_serialize_person_for_recommendations(person)))
    engine.run()
    recommendations = engine.get_recommendations()
    if not recommendations:
        return ["Додаткові рекомендації відсутні на основі введених даних."]
    return list(recommendations)


def _format_recommendation_categories(categories: Iterable[str]) -> List[str]:
    order = [
        ("conscripts", "призовників"),
        ("liable", "військовозобовʼязаних"),
        ("reservists", "резервістів"),
    ]
    categories_set = {value for value in categories if value}
    return [label for key, label in order if key in categories_set]


def _build_recommendations_selection_summary(selected_count: int, categories: Sequence[str]) -> str:
    categories = list(categories or [])
    if "all" in categories:
        return "Для формування вибрано усі записи."

    category_labels = _format_recommendation_categories(categories)
    if category_labels:
        joined = ", ".join(category_labels)
        return f"Для формування вибрано записи всіх {joined}."

    noun = "запис"
    if selected_count != 1:
        noun = "записів"
    return f"Для формування вибрано {selected_count} {noun}."


def _build_recommendations_bulk_context(
    persons: Sequence[Person],
    *,
    selection_summary: Optional[str] = None,
    selection_categories: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    persons_list = list(persons)
    entries = []
    for person in persons_list:
        name_parts = [
            part.strip()
            for part in (
                person.last_name,
                person.first_name,
                person.middle_name or "",
            )
            if part
        ]
        full_name = " ".join(name_parts).strip() or str(person).strip() or "—"
        entries.append(
            {
                "person": person,
                "full_name": full_name,
                "edrpvr_number": person.edrpvr_number or "—",
                "recommendations": _build_person_recommendations(person),
            }
        )
    return {
        "recommendations_entries": entries,
        "selected_count": len(persons_list),
        "selected_persons": persons_list,
        "selected_person_ids": [person.pk for person in persons_list],
        "primary_color": PRIMARY_COLOR,
        "generated_on": timezone.localdate(),
        "generated_at": timezone.localtime(),
        "selection_summary": selection_summary or _build_recommendations_selection_summary(
            len(persons_list),
            selection_categories or [],
        ),
        "selection_categories": list(selection_categories or []),
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


class PersonRulesBulkView(LoginRequiredMixin, SidebarContextMixin, FormView):
    template_name = "persons/person_rules_bulk_select.html"
    form_class = RulesAcknowledgementSelectionForm
    sidebar_active = "rules_bulk"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["persons_total"] = Person.objects.count()
        queryset = context["form"].fields["persons"].queryset if "form" in context else Person.objects.all()
        context["persons_edrpvr"] = {
            str(person.pk): (person.edrpvr_number or "—")
            for person in queryset
        }
        context["persons_categories"] = {
            str(person.pk): person.account_category
            for person in queryset
        }
        return context

    def form_valid(self, form: RulesAcknowledgementSelectionForm) -> HttpResponse:
        selected_persons = form.get_selected_persons()
        if not selected_persons:
            form.add_error(None, "За вибраними умовами осіб не знайдено.")
            return self.form_invalid(form)
        context = _build_rules_bulk_context(selected_persons)
        context["sidebar_active"] = self.sidebar_active
        context["selection_form"] = form
        return render(self.request, "persons/person_rules_bulk.html", context)


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


class PersonRulesBulkPdfView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        person_ids = request.POST.getlist("person_ids")
        if not person_ids:
            messages.error(request, "Не вдалося сформувати PDF — не передано жодного запису.")
            return HttpResponseRedirect(reverse("persons:person_rules_bulk"))

        try:
            numeric_ids = [int(pk) for pk in person_ids]
        except ValueError:
            messages.error(request, "Передані некоректні ідентифікатори записів.")
            return HttpResponseRedirect(reverse("persons:person_rules_bulk"))

        ordering = Person._meta.ordering or ["last_name", "first_name", "middle_name"]
        persons = list(Person.objects.filter(pk__in=numeric_ids).order_by(*ordering))
        if not persons:
            messages.error(request, "За вибраними умовами осіб не знайдено.")
            return HttpResponseRedirect(reverse("persons:person_rules_bulk"))

        html_renderer = _get_weasyprint_html()
        if html_renderer is None:
            return HttpResponse(
                "PDF generation is unavailable. Please install WeasyPrint.",
                status=503,
            )

        context = _build_rules_bulk_context(persons)
        context["request"] = request
        html = render_to_string("persons/person_rules_bulk_pdf.html", context)
        pdf_bytes = html_renderer(
            string=html,
            base_url=request.build_absolute_uri("/"),
        ).write_pdf()
        filename = slugify("pravila-bagatoh-osib") or "pravila"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response


class PersonRecommendationsBulkView(LoginRequiredMixin, SidebarContextMixin, FormView):
    template_name = "persons/person_recommendations_select.html"
    form_class = RulesAcknowledgementSelectionForm
    sidebar_active = "recommendations"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["persons_total"] = Person.objects.count()
        queryset = context["form"].fields["persons"].queryset if "form" in context else Person.objects.all()
        context["persons_edrpvr"] = {
            str(person.pk): (person.edrpvr_number or "—")
            for person in queryset
        }
        context["persons_categories"] = {
            str(person.pk): person.account_category
            for person in queryset
        }
        return context

    def form_valid(self, form: RulesAcknowledgementSelectionForm) -> HttpResponse:
        selected_persons = form.get_selected_persons()
        if not selected_persons:
            form.add_error(None, "За вибраними умовами осіб не знайдено.")
            return self.form_invalid(form)
        selected_categories = form.cleaned_data.get("bulk_options", [])
        selection_summary = _build_recommendations_selection_summary(
            len(selected_persons),
            selected_categories,
        )
        context = _build_recommendations_bulk_context(
            selected_persons,
            selection_summary=selection_summary,
            selection_categories=selected_categories,
        )
        context["sidebar_active"] = self.sidebar_active
        context["selection_form"] = form
        context["selected_categories"] = list(selected_categories or [])
        return render(self.request, "persons/person_recommendations_bulk.html", context)


class PersonRecommendationsBulkPdfView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        person_ids = request.POST.getlist("person_ids")
        if not person_ids:
            messages.error(request, "Не вдалося сформувати PDF — не передано жодного запису.")
            return HttpResponseRedirect(reverse("persons:person_recommendations_bulk"))

        try:
            numeric_ids = [int(pk) for pk in person_ids]
        except ValueError:
            messages.error(request, "Передані некоректні ідентифікатори записів.")
            return HttpResponseRedirect(reverse("persons:person_recommendations_bulk"))

        ordering = Person._meta.ordering or ["last_name", "first_name", "middle_name"]
        persons = list(Person.objects.filter(pk__in=numeric_ids).order_by(*ordering))
        if not persons:
            messages.error(request, "За вибраними умовами осіб не знайдено.")
            return HttpResponseRedirect(reverse("persons:person_recommendations_bulk"))

        html_renderer = _get_weasyprint_html()
        if html_renderer is None:
            return HttpResponse(
                "PDF generation is unavailable. Please install WeasyPrint.",
                status=503,
            )

        posted_categories = request.POST.getlist("selected_categories")
        posted_summary = request.POST.get("selection_summary") or None
        if not posted_summary:
            posted_summary = _build_recommendations_selection_summary(len(persons), posted_categories)

        context = _build_recommendations_bulk_context(
            persons,
            selection_summary=posted_summary,
            selection_categories=posted_categories,
        )
        context["request"] = request
        html = render_to_string("persons/person_recommendations_bulk_pdf.html", context)
        pdf_bytes = html_renderer(
            string=html,
            base_url=request.build_absolute_uri("/"),
        ).write_pdf()
        filename = slugify("rekomendatsii-bagatoh-osib") or "rekomendatsii"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response
