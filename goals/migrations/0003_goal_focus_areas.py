from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0002_goal_assigned_exercises'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='focus_areas',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
