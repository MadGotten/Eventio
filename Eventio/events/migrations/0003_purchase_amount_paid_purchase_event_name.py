# Generated by Django 5.2.4 on 2025-07-20 23:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0002_alter_review_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="amount_paid",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="purchase",
            name="event_name",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
    ]
