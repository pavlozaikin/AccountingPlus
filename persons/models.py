from __future__ import annotations

from django.db import models
from django.urls import reverse


class Person(models.Model):
    GENDER_CHOICES = [
        ("male", "Чоловік"),
        ("female", "Жінка"),
    ]
    CATEGORY_CHOICES = [
        ("призовник", "призовник"),
        ("військовозобовʼязаний", "військовозобовʼязаний"),
        ("резервіст", "резервіст"),
    ]

    last_name = models.CharField("Прізвище", max_length=150)
    first_name = models.CharField("Імʼя", max_length=150)
    middle_name = models.CharField("По батькові", max_length=150, blank=True)
    gender = models.CharField("Стать", max_length=10, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField("Дата народження", blank=True, null=True)
    rnokpp = models.CharField("РНОКПП", max_length=10, blank=True)
    address_registered = models.CharField(
        "Адреса задекларованого/зареєстрованого місця проживання",
        max_length=255,
        blank=True,
    )
    address_actual = models.CharField(
        "Адреса фактичного місця проживання",
        max_length=255,
        blank=True,
    )
    phone = models.CharField("Телефон", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)

    position_name = models.CharField("Найменування посади", max_length=255, blank=True)
    appoint_order_date = models.DateField(
        "Дата наказу про призначення",
        blank=True,
        null=True,
    )
    dismiss_order_date = models.DateField(
        "Дата наказу про звільнення",
        blank=True,
        null=True,
    )

    account_category = models.CharField(
        "Категорія військового обліку",
        max_length=32,
        choices=CATEGORY_CHOICES,
        default="призовник",
    )
    mil_rank = models.CharField("Військове звання", max_length=100, blank=True)
    vos_code = models.CharField("Цифрове позначення ВОС", max_length=6, blank=True)

    tcksp = models.CharField("ТЦК та СП", max_length=150, blank=True)
    edrpvr_number = models.CharField("Номер у ЄДРПВР", max_length=100, blank=True)
    doc_type = models.CharField("Тип", max_length=100, blank=True)
    doc_series_number = models.CharField("(Серія) та номер", max_length=100, blank=True)

    passport_series_number = models.CharField(
        "(Серія) та номер паспорта",
        max_length=100,
        blank=True,
    )
    passport_issued_by = models.CharField("Ким видано паспорт", max_length=200, blank=True)
    passport_issued_date = models.DateField(
        "Дата видачі паспорта",
        blank=True,
        null=True,
    )

    deferral_until = models.DateField("Відстрочка до", blank=True, null=True)
    deferral_reason = models.TextField("Підстава відстрочки", blank=True)
    booking_until = models.DateField("Бронювання до", blank=True, null=True)

    mobil_order_date = models.DateField("Дата видачі мобілізаційного розпорядження", blank=True, null=True)
    unit_number = models.CharField("Номер військової частини", max_length=100, blank=True)

    notif_appoint_date = models.DateField("Повідомлення про призначення", blank=True, null=True)
    notif_dismiss_date = models.DateField("Повідомлення про звільнення", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "middle_name"]
        verbose_name = "Особа"
        verbose_name_plural = "Особи"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def get_absolute_url(self) -> str:
        return reverse("persons:person_update", args=[self.pk])
