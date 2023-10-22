# This scripts ingest rows to the Heroes table as defined in core/models.py

from django.db import migrations
from pathlib import Path
import pandas as pd
import os


def ingest_heroes(apps, schema_editor):
    BASEPATH = Path(__file__).resolve().parent.parent.parent.parent
    resource_path = os.path.join(BASEPATH, "Valve_resources", "hero_wide_icons")
    df = pd.read_csv(os.path.join(resource_path, "names.csv"), header=0, index_col=None)
    print(df.columns)
    df['image'] = [resource_path + x + ".png" for x in df['alt_name']]
    target = apps.get_model("core", "Hero")
    for index, row in df.iterrows():
        target.objects.create(
            name=row['name'],
            alt_name=row['alt_name'],
            primary_attribute=row['primary_attribute'],
            image=row['image'],
        )

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ingest_heroes),
    ]
