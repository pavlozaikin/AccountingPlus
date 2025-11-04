from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Person


COMMON_INPUT_CLASSES = "form-control"
COMMON_SELECT_CLASSES = "form-select"


class AccountingAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Електронна пошта або імʼя користувача",
        widget=forms.TextInput(
            attrs={"autofocus": True, "placeholder": "name@example.com", "class": COMMON_INPUT_CLASSES}
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
            css_class = field.widget.attrs.get("class", "")
            if self.errors.get(name):
                field.widget.attrs["class"] = f"{css_class} is-invalid".strip()


class DateInput(forms.DateInput):
    input_type = "date"


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
        for field_name, field in self.fields.items():
            if field_name in self.Meta.widgets:
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", COMMON_SELECT_CLASSES)
            else:
                field.widget.attrs.setdefault("class", COMMON_INPUT_CLASSES)
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.setdefault("autocomplete", "off")
        if self.is_bound:
            for name, field in self.fields.items():
                if field.errors:
                    css_class = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{css_class} is-invalid".strip()

    def get_recommendation_payload(self) -> dict[str, Any]:
        cleaned_data = {name: self.cleaned_data.get(name) for name in self.Meta.fields}
        return cleaned_data
