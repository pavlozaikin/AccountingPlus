from __future__ import annotations

from typing import Any, Dict, List, cast

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.formats import get_format

from .models import Person


COMMON_INPUT_CLASSES = "form-control"
COMMON_SELECT_CLASSES = "form-select"


def _ensure_widget_attrs(field: forms.Field) -> Dict[str, Any]:
    """Return a mutable attrs dict for the field's widget."""
    widget = cast(forms.Widget, field.widget)
    attrs = getattr(widget, "attrs", None)
    if not isinstance(attrs, dict):
        attrs = dict(attrs or {})
    setattr(widget, "attrs", attrs)
    return attrs


class AccountingAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Імʼя користувача",
        widget=forms.TextInput(
            attrs={"autofocus": True, "placeholder": "username", "class": COMMON_INPUT_CLASSES}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "••••••••", "class": COMMON_INPUT_CLASSES}
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            attrs = _ensure_widget_attrs(field)
            css_class = attrs.get("class", "")
            errors = self.errors
            if errors and errors.get(name):
                attrs["class"] = f"{css_class} is-invalid".strip()


DATE_INPUT_FORMAT = "%Y-%m-%d"


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("format", DATE_INPUT_FORMAT)
        super().__init__(*args, **kwargs)


def _get_date_input_formats() -> List[str]:
    formats: List[str] = [DATE_INPUT_FORMAT]
    for fmt in get_format("DATE_INPUT_FORMATS"):
        fmt_str = str(fmt)
        if fmt_str not in formats:
            formats.append(fmt_str)
    return formats


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "birth_date",
            "rnokpp",
            "address_registered",
            "address_actual",
            "phone",
            "email",
            "position_name",
            "appoint_order_date",
            "dismiss_order_date",
            "account_category",
            "mil_rank",
            "vos_code",
            "tcksp",
            "edrpvr_number",
            "doc_type",
            "doc_series_number",
            "passport_series_number",
            "passport_issued_by",
            "passport_issued_date",
            "deferral_until",
            "deferral_reason",
            "booking_until",
            "mobil_order_date",
            "unit_number",
            "notif_appoint_date",
            "notif_dismiss_date",
        ]
        widgets = {
            "birth_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "appoint_order_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "dismiss_order_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "passport_issued_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "deferral_until": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "booking_until": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "mobil_order_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "notif_appoint_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "notif_dismiss_date": DateInput(attrs={"class": COMMON_INPUT_CLASSES}),
            "deferral_reason": forms.Textarea(attrs={"class": COMMON_INPUT_CLASSES, "rows": 2}),
            "account_category": forms.Select(attrs={"class": COMMON_SELECT_CLASSES}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        date_input_formats = _get_date_input_formats()
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                field.input_formats = list(date_input_formats)
            if field_name in self.Meta.widgets:
                continue
            if isinstance(field.widget, forms.Select):
                attrs = _ensure_widget_attrs(field)
                attrs.setdefault("class", COMMON_SELECT_CLASSES)
            else:
                attrs = _ensure_widget_attrs(field)
                attrs.setdefault("class", COMMON_INPUT_CLASSES)
            if isinstance(field.widget, forms.TextInput):
                attrs = _ensure_widget_attrs(field)
                attrs.setdefault("autocomplete", "off")
        if self.is_bound:
            for name, field in self.fields.items():
                bound_field = self[name]
                if bound_field.errors:
                    attrs = _ensure_widget_attrs(field)
                    css_class = attrs.get("class", "")
                    attrs["class"] = f"{css_class} is-invalid".strip()

    def get_recommendation_payload(self) -> dict[str, Any]:
        cleaned_data = {name: self.cleaned_data.get(name) for name in self.Meta.fields}
        return cleaned_data
