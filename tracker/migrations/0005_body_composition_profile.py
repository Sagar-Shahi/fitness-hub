from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [('tracker', '0004_personal_nutrition_profile')]

    operations = [
        migrations.AddField(
            model_name='profile', name='body_type',
            field=models.CharField(blank=True, choices=[('ectomorph', 'Ectomorph / naturally lean'), ('mesomorph', 'Mesomorph / naturally muscular'), ('endomorph', 'Endomorph / naturally rounder build'), ('unsure', 'Not sure')], max_length=12),
        ),
        migrations.AddField(
            model_name='profile', name='body_fat_percentage',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(75)]),
        ),
        migrations.AddField(
            model_name='profile', name='waist_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(200)]),
        ),
        migrations.AddField(
            model_name='profile', name='muscle_mass_kg',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(150)]),
        ),
    ]
