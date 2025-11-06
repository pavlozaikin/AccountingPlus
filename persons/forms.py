from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, cast

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.formats import get_format

from .models import Person
from .tck_reference_data import get_tck_names


COMMON_INPUT_CLASSES = "form-control"
COMMON_SELECT_CLASSES = "form-select"
DOC_TYPE_CHOICES = [
    ("", "Оберіть тип"),
    ("Військово-обліковий документ", "Військово-обліковий документ (паперовий)"),
    ("Резерв+", "Резерв+"),
    ("Тимчасове посвідчення військовозобовʼязаного", "Тимчасове посвідчення військовозобовʼязаного"),
    ("Військовий квиток", "Військовий квиток"),
    ("Приписне посвідчення", "Приписне посвідчення"),
]
DOC_TYPE_NUMBER_ONLY_VALUES = {
    "Військово-обліковий документ",
    "Резерв+",
}
DEFAULT_DOC_SERIES_LABEL = "Серія та номер"
DEFAULT_DOC_NUMBER_LABEL = "Номер"
DEFAULT_DOC_SERIES_PLACEHOLDER = "Введіть серію та номер"
DEFAULT_DOC_NUMBER_PLACEHOLDER = "Введіть номер"
DEFAULT_PASSPORT_SERIES_LABEL = "Серія та номер"
DEFAULT_PASSPORT_NUMBER_LABEL = "Номер"
RULES_BULK_CHOICES = [
    ("all", "Усі"),
    ("conscripts", "Призовники"),
    ("liable", "Військовозобовʼязані"),
    ("reservists", "Резервісти"),
]


def _ensure_widget_attrs(field: forms.Field) -> Dict[str, Any]:
    """Return a mutable attrs dict for the field's widget."""
    widget = cast(forms.Widget, field.widget)
    attrs = getattr(widget, "attrs", None)
    if not isinstance(attrs, dict):
        attrs = dict(attrs or {})
    setattr(widget, "attrs", attrs)
    return attrs


class TckAutocompleteWidget(forms.TextInput):
    template_name = "persons/widgets/tck_autocomplete.html"

    def __init__(
        self,
        *args: Any,
        datalist_id: str = "tcksp-options",
        choices: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.datalist_id = datalist_id
        self.choices = list(choices or [])
        self.options_data_id = f"{self.datalist_id}-data"

    def get_context(self, name: str, value: Any, attrs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        widget_attrs = widget.setdefault("attrs", {})
        widget_attrs.setdefault("list", self.datalist_id)
        widget_attrs.setdefault("data-tck-autocomplete", "true")
        widget_attrs.setdefault("data-tck-options-id", self.options_data_id)
        widget["options"] = self.choices
        widget["datalist_id"] = self.datalist_id
        widget["options_data_id"] = self.options_data_id
        return context


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


class AccountPasswordChangeForm(PasswordChangeForm):
    """Password change form with consistent styling."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        labels = {
            "old_password": "Поточний пароль",
            "new_password1": "Новий пароль",
            "new_password2": "Підтвердження нового пароля",
        }
        autocompletes = {
            "old_password": "current-password",
            "new_password1": "new-password",
            "new_password2": "new-password",
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            attrs = _ensure_widget_attrs(field)
            attrs.setdefault("class", COMMON_INPUT_CLASSES)
            attrs.setdefault("autocomplete", autocompletes.get(name, "off"))
            attrs.setdefault("placeholder", field.label)
            if name != "old_password":
                field.strip = False
            if name in self.errors:
                classes = attrs.get("class", "").strip()
                attrs["class"] = f"{classes} is-invalid".strip()


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
            "gender",
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
            "passport_type",
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
            "gender": forms.Select(attrs={"class": COMMON_SELECT_CLASSES}),
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
            "doc_type": forms.Select(attrs={"class": COMMON_SELECT_CLASSES}),
            "passport_type": forms.Select(attrs={"class": COMMON_SELECT_CLASSES}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        gender_field = self.fields.get("gender")
        if gender_field is not None:
            gender_field.choices = [("", "Оберіть стать")] + list(Person.GENDER_CHOICES)
        tcksp_field = self.fields.get("tcksp")
        if tcksp_field is not None:
            widget = TckAutocompleteWidget(
                choices=get_tck_names(),
                attrs={"placeholder": "Почніть вводити назву ТЦК та СП"},
            )
            tcksp_field.widget = widget
        doc_type_field = self.fields.get("doc_type")
        if doc_type_field is not None and isinstance(doc_type_field.widget, forms.Select):
            doc_type_choices = list(DOC_TYPE_CHOICES)
            current_value = self.initial.get("doc_type") or getattr(self.instance, "doc_type", "")
            if current_value and all(value != current_value for value, _ in DOC_TYPE_CHOICES):
                doc_type_choices.append((current_value, current_value))
            doc_type_field.widget.choices = doc_type_choices
        doc_series_field = self.fields.get("doc_series_number")
        edrpvr_field = self.fields.get("edrpvr_number")
        passport_type_field = self.fields.get("passport_type")
        passport_series_field = self.fields.get("passport_series_number")
        doc_type_value: str = ""
        if doc_type_field is not None:
            doc_type_key = self.add_prefix("doc_type")
            if self.is_bound:
                doc_type_value = str(self.data.get(doc_type_key, "")).strip()
            else:
                doc_type_value = str(
                    self.initial.get("doc_type") or getattr(self.instance, "doc_type", "")
                ).strip()
        passport_type_value: str = ""
        if passport_type_field is not None:
            passport_type_key = self.add_prefix("passport_type")
            if self.is_bound:
                passport_type_value = str(self.data.get(passport_type_key, "")).strip()
            else:
                passport_type_value = str(
                    self.initial.get("passport_type") or getattr(self.instance, "passport_type", "")
                ).strip()
        if doc_series_field is not None:
            doc_series_attrs = _ensure_widget_attrs(doc_series_field)
            doc_series_attrs.setdefault("data-label-number", DEFAULT_DOC_NUMBER_LABEL)
            doc_series_attrs.setdefault("data-label-series", DEFAULT_DOC_SERIES_LABEL)
            doc_series_attrs.setdefault("data-placeholder-number", DEFAULT_DOC_NUMBER_PLACEHOLDER)
            doc_series_attrs.setdefault("data-placeholder-series", DEFAULT_DOC_SERIES_PLACEHOLDER)
            if edrpvr_field is not None:
                edrpvr_auto_id = self["edrpvr_number"].auto_id
                if edrpvr_auto_id:
                    doc_series_attrs.setdefault("data-edrpvr-input-id", edrpvr_auto_id)
            if doc_type_field is not None:
                doc_type_auto_id = self["doc_type"].auto_id
                if doc_type_auto_id:
                    doc_series_attrs.setdefault("data-doc-type-input-id", doc_type_auto_id)
            if doc_type_value in DOC_TYPE_NUMBER_ONLY_VALUES:
                doc_series_field.label = DEFAULT_DOC_NUMBER_LABEL
                doc_series_attrs["placeholder"] = DEFAULT_DOC_NUMBER_PLACEHOLDER
            else:
                doc_series_field.label = DEFAULT_DOC_SERIES_LABEL
                doc_series_attrs["placeholder"] = DEFAULT_DOC_SERIES_PLACEHOLDER
        if passport_series_field is not None:
            passport_series_attrs = _ensure_widget_attrs(passport_series_field)
            passport_series_attrs.setdefault("data-label-number", DEFAULT_PASSPORT_NUMBER_LABEL)
            passport_series_attrs.setdefault("data-label-series", DEFAULT_PASSPORT_SERIES_LABEL)
            passport_series_attrs.setdefault("data-passport-type-value-book", Person.PASSPORT_TYPE_BOOK)
            passport_series_attrs.setdefault("data-passport-type-value-id", Person.PASSPORT_TYPE_ID_CARD)
            if passport_type_field is not None:
                passport_type_auto_id = self["passport_type"].auto_id
                if passport_type_auto_id:
                    passport_series_attrs.setdefault("data-passport-type-input-id", passport_type_auto_id)
            if passport_type_value == Person.PASSPORT_TYPE_ID_CARD:
                passport_series_field.label = DEFAULT_PASSPORT_NUMBER_LABEL
            else:
                passport_series_field.label = DEFAULT_PASSPORT_SERIES_LABEL
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


class RulesAcknowledgementSelectionForm(forms.Form):
    bulk_options = forms.MultipleChoiceField(
        label="Швидкий вибір",
        required=False,
        choices=RULES_BULK_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    persons = forms.ModelMultipleChoiceField(
        label="Загальний список",
        queryset=Person.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    error_messages = {
        "empty_selection": "Оберіть хоча б одну особу або категорію.",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        ordering = Person._meta.ordering or ["last_name", "first_name", "middle_name"]
        self.fields["persons"].queryset = Person.objects.order_by(*ordering)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                attrs = _ensure_widget_attrs(field)
                attrs.setdefault("class", "form-check-list")
                if name == "persons":
                    attrs.setdefault("data-rules-bulk-checkbox", "true")

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        selected_persons = cleaned_data.get("persons")
        bulk_options = cleaned_data.get("bulk_options")
        if not selected_persons and not bulk_options:
            raise forms.ValidationError(self.error_messages["empty_selection"])
        return cleaned_data

    def get_selected_persons(self) -> List[Person]:
        if not hasattr(self, "cleaned_data"):
            return []
        selected_ids: set[int] = set()
        person_qs = self.cleaned_data.get("persons")
        if person_qs:
            selected_ids.update(person_qs.values_list("pk", flat=True))
        bulk_options = set(self.cleaned_data.get("bulk_options", []))
        base_qs = Person.objects.all()
        if "all" in bulk_options:
            selected_ids.update(base_qs.values_list("pk", flat=True))
        else:
            if "conscripts" in bulk_options:
                selected_ids.update(
                    base_qs.filter(account_category="призовник").values_list("pk", flat=True)
                )
            if "liable" in bulk_options:
                selected_ids.update(
                    base_qs.filter(account_category="військовозобовʼязаний").values_list("pk", flat=True)
                )
            if "reservists" in bulk_options:
                selected_ids.update(
                    base_qs.filter(account_category="резервіст").values_list("pk", flat=True)
                )
        if not selected_ids:
            return []
        ordering = Person._meta.ordering or ["last_name", "first_name", "middle_name"]
        return list(Person.objects.filter(pk__in=selected_ids).order_by(*ordering))
