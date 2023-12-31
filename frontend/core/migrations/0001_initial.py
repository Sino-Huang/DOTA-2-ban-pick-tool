# Generated by Django 4.2.6 on 2023-10-22 15:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Attribute",
            fields=[
                (
                    "name",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("order", models.IntegerField()),
                ("image", models.ImageField(blank=True, upload_to="attribute_images")),
            ],
            options={"verbose_name_plural": "Attributes", "ordering": ("order",),},
        ),
        migrations.CreateModel(
            name="Hero",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("alt_name", models.CharField(max_length=100)),
                ("image", models.ImageField(blank=True, upload_to="hero_images")),
                (
                    "primary_attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.attribute"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Heroes",
                "ordering": ("primary_attribute", "name"),
            },
        ),
    ]
