# Generated for FitHub's shared research cache.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0002_exercise_set'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResearchCacheEntry',
            fields=[
                ('cache_key', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('expires', models.DateTimeField(db_index=True)),
            ],
            options={
                'db_table': 'fithub_research_cache',
            },
        ),
    ]
