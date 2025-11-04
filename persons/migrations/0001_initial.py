from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_name", models.CharField(max_length=150, verbose_name="Прізвище")),
                ("first_name", models.CharField(max_length=150, verbose_name="Імʼя")),
                ("middle_name", models.CharField(blank=True, max_length=150, verbose_name="По батькові")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="Дата народження")),
                ("rnokpp", models.CharField(blank=True, max_length=20, verbose_name="РНОКПП")),
                (
                    "address_registered",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Адреса задекларованого/зареєстрованого місця проживання",
                    ),
                ),
                (
                    "address_actual",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Адреса фактичного місця проживання",
                    ),
                ),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="Телефон")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Email")),
                ("position_name", models.CharField(blank=True, max_length=255, verbose_name="Найменування посади")),
                (
                    "appoint_order_date",
                    models.DateField(blank=True, null=True, verbose_name="Дата наказу про призначення"),
                ),
                (
                    "dismiss_order_date",
                    models.DateField(blank=True, null=True, verbose_name="Дата наказу про звільнення"),
                ),
                (
                    "account_category",
                    models.CharField(
                        choices=[
                            ("призовник", "призовник"),
                            ("військовозобовʼязаний", "військовозобовʼязаний"),
                            ("резервіст", "резервіст"),
                        ],
                        default="призовник",
                        max_length=32,
                        verbose_name="Категорія військового обліку",
                    ),
                ),
                ("mil_rank", models.CharField(blank=True, max_length=100, verbose_name="Військове звання")),
                ("vos_code", models.CharField(blank=True, max_length=50, verbose_name="Цифрове позначення ВОС")),
                ("tcksp", models.CharField(blank=True, max_length=150, verbose_name="ТЦК та СП")),
                ("edrpvr_number", models.CharField(blank=True, max_length=100, verbose_name="Номер у ЄДРПВР")),
                ("doc_type", models.CharField(blank=True, max_length=100, verbose_name="Тип")),
                ("doc_series_number", models.CharField(blank=True, max_length=100, verbose_name="(Серія) та номер")),
                (
                    "passport_series_number",
                    models.CharField(blank=True, max_length=100, verbose_name="(Серія) та номер паспорта"),
                ),
                ("passport_issued_by", models.CharField(blank=True, max_length=200, verbose_name="Ким видано паспорт")),
                (
                    "passport_issued_date",
                    models.DateField(blank=True, null=True, verbose_name="Дата видачі паспорта"),
                ),
                ("deferral_until", models.DateField(blank=True, null=True, verbose_name="Відстрочка до")),
                ("deferral_reason", models.TextField(blank=True, verbose_name="Підстава відстрочки")),
                ("booking_until", models.DateField(blank=True, null=True, verbose_name="Бронювання до")),
                (
                    "mobil_order_date",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Дата видачі мобілізаційного розпорядження",
                    ),
                ),
                ("unit_number", models.CharField(blank=True, max_length=100, verbose_name="Номер військової частини")),
                (
                    "notif_appoint_date",
                    models.DateField(blank=True, null=True, verbose_name="Повідомлення про призначення"),
                ),
                (
                    "notif_dismiss_date",
                    models.DateField(blank=True, null=True, verbose_name="Повідомлення про звільнення"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Особа",
                "verbose_name_plural": "Особи",
                "ordering": ["last_name", "first_name", "middle_name"],
            },
        ),
    ]
