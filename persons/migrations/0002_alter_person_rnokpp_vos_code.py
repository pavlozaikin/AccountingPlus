from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="rnokpp",
            field=models.CharField(blank=True, max_length=10, verbose_name="РНОКПП"),
        ),
        migrations.AlterField(
            model_name="person",
            name="vos_code",
            field=models.CharField(blank=True, max_length=6, verbose_name="Цифрове позначення ВОС"),
        ),
    ]
