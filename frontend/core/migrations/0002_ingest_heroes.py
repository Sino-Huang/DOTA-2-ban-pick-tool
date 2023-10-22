# This scripts ingest rows to the Heroes table as defined in core/models.py

from django.db import migrations
from pathlib import Path
import pandas as pd
import os

def ingest_attributes(apps, schema_editor):
    attributes = [
        ('Strength', 1, 'hero_strength.png'),
        ('Agility', 2, 'hero_agility.png'),
        ('Intelligence', 3, 'hero_intelligence.png'),
        ('Universal', 4, 'hero_universal.png'),
    ]
    target = apps.get_model("core", "Attribute")
    for attribute in attributes:
        target.objects.create(
            name=attribute[0],
            order=attribute[1],
            image=os.path.join('attribute_images', attribute[2]),
        )


def ingest_heroes(apps, schema_editor):
    BASEPATH = Path(__file__).resolve().parent.parent.parent.parent
    resource_path = os.path.join(BASEPATH, "Valve_resources", "hero_wide_icons")
    df = pd.read_csv(os.path.join(resource_path, "names.csv"), header=0, index_col=None)
    df['image'] = [os.path.join('hero_images', x + '.png') for x in df['alt_name']]
    target = apps.get_model("core", "Hero")
    for index, row in df.iterrows():
        target.objects.create(
            name=row['name'],
            alt_name=row['alt_name'],
            primary_attribute_id=row['primary_attribute'],
            image=row['image'],
        )

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ingest_attributes),
        migrations.RunPython(ingest_heroes),
    ]
