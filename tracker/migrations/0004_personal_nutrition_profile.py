from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [('tracker', '0003_research_cache')]

    operations = [
        migrations.AddField(
            model_name='profile', name='age',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(13), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='profile', name='height_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(120), django.core.validators.MaxValueValidator(230)]),
        ),
        migrations.AddField(
            model_name='profile', name='starting_weight_kg',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(300)]),
        ),
        migrations.AddField(
            model_name='profile', name='sex_for_calculation',
            field=models.CharField(blank=True, choices=[('female', 'Female'), ('male', 'Male'), ('other', 'Other / prefer not to say')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile', name='activity_level',
            field=models.CharField(blank=True, choices=[('sedentary', 'Mostly sitting / little exercise'), ('light', 'Light activity (1–3 days/week)'), ('moderate', 'Moderate activity (3–5 days/week)'), ('very_active', 'Very active (6–7 days/week)')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile', name='training_type',
            field=models.CharField(blank=True, choices=[('strength', 'Strength / muscle building'), ('cardio', 'Cardio / endurance'), ('mixed', 'Mixed strength and cardio'), ('general', 'General fitness')], max_length=12),
        ),
        migrations.AddField(
            model_name='profile', name='nutrition_goal',
            field=models.CharField(blank=True, choices=[('fat_loss', 'Fat loss'), ('maintain', 'Weight maintenance'), ('muscle_gain', 'Muscle gain')], default='maintain', max_length=12),
        ),
    ]
