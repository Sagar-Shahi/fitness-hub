from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

STAFF_GROUP_NAME = 'Staff (no user management)'

EXCLUDED_MODELS = {
    ('auth', 'user'),
    ('auth', 'group'),
    ('auth', 'permission'),
    ('users', 'profile'),
}


class Command(BaseCommand):
    help = 'Create permission groups for staff users (excludes user management).'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=STAFF_GROUP_NAME)

        excluded_cts = ContentType.objects.filter(
            app_label__in={app for app, _ in EXCLUDED_MODELS},
            model__in={model for _, model in EXCLUDED_MODELS},
        )
        excluded_perms = Permission.objects.filter(content_type__in=excluded_cts)

        allowed_perms = Permission.objects.exclude(pk__in=excluded_perms.values('pk'))
        group.permissions.set(allowed_perms)

        self.stdout.write(self.style.SUCCESS(
            f'Group "{STAFF_GROUP_NAME}" ready — {allowed_perms.count()} permissions assigned.'
        ))
        self.stdout.write()
        self.stdout.write('How to use:')
        self.stdout.write('  1. Keep YOUR account as superuser (you manage users).')
        self.stdout.write('  2. Create other staff users via the admin panel.')
        self.stdout.write('  3. Set them as "Staff status" (is_staff=True), NOT superuser.')
        self.stdout.write(f'  4. Add them to the "{STAFF_GROUP_NAME}" group.')
        self.stdout.write()
        self.stdout.write('They will be able to manage everything except:')
        for app_label, model in sorted(EXCLUDED_MODELS):
            self.stdout.write(f'     - {app_label}.{model}')
