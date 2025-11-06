from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0002_alter_person_rnokpp_vos_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("male", "Чоловік"), ("female", "Жінка")],
                max_length=10,
                verbose_name="Стать",
            ),
        ),
    ]
