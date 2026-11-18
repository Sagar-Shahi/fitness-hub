# Generated for individual-set workout tracking.
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def copy_legacy_exercise_summaries(apps, schema_editor):
    Exercise = apps.get_model('tracker', 'Exercise')
    ExerciseSet = apps.get_model('tracker', 'ExerciseSet')
    batch = []
    for exercise in Exercise.objects.all().iterator():
        for number in range(1, exercise.sets + 1):
            batch.append(ExerciseSet(
                exercise_id=exercise.pk,
                set_number=number,
                reps=exercise.reps,
                weight_kg=exercise.weight_kg,
                is_completed=True,
                is_warmup=False,
            ))
        if len(batch) >= 1000:
            ExerciseSet.objects.bulk_create(batch, batch_size=1000)
            batch = []
    if batch:
        ExerciseSet.objects.bulk_create(batch, batch_size=1000)


class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_number', models.PositiveSmallIntegerField(
                    validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(50)],
                )),
                ('reps', models.PositiveSmallIntegerField(
                    validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(500)],
                )),
                ('weight_kg', models.DecimalField(
                    decimal_places=1, default=0, max_digits=5,
                    validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1000)],
                )),
                ('is_completed', models.BooleanField(default=False)),
                ('is_warmup', models.BooleanField(default=False)),
                ('exercise', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='set_entries',
                    to='tracker.exercise',
                )),
            ],
            options={'ordering': ['set_number', 'id']},
        ),
        migrations.AddConstraint(
            model_name='exerciseset',
            constraint=models.UniqueConstraint(
                fields=('exercise', 'set_number'),
                name='unique_exercise_set_number',
            ),
        ),
        migrations.RunPython(copy_legacy_exercise_summaries, migrations.RunPython.noop),
    ]
