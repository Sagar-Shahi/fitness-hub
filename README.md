# Final-Project

Fitness Hub - Django Fitness Platform by Sagar 

Quick start:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_store
python manage.py seed_exercises
python manage.py seed_gamification
python manage.py seed_inspiration
python manage.py seed_groups
python manage.py runserver
```

This creates a "Staff (no user management)" group. Keep your account as superuser
(to manage users), and add other team members to this group as staff (not superuser).
They'll have access to everything except user/group/permission management.

## Configuration (keeping secrets out of git)

Secrets and per-machine settings are read from environment variables, which you can keep in a local `.env` file.
`.env` is ignored by git, so it is never committed.

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
# paste the printed value after DJANGO_SECRET_KEY= in .env
```

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Signs sessions and cookies. Required when `DJANGO_DEBUG=False` |
| `DJANGO_DEBUG` | `True` for local development (default), `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma separated hostnames the site may be served from |

Local development works without a `.env` file, using a clearly marked insecure development key.

Features implemented:
- User Profile with edit
- Dashboard basic chart
- Goals CRUD
- Nutrition (Diet) CRUD
- Progress CRUD
- Exercise library (seeded)
- Store with cart (session), checkout simulation

Next steps: polish UI, add tests, and integrate payments.
 
CI: A GitHub Actions workflow was added at `.github/workflows/ci.yml` to run migrations and tests on push/PR to `main`.

Run tests locally:

```bash
python manage.py test
```

Payments (Stripe test mode):

The project includes a placeholder Stripe Checkout integration. To enable it locally or in CI, set the `STRIPE_SECRET_KEY` environment variable to your Stripe test secret key. When set, the checkout flow will redirect to Stripe Checkout; otherwise the checkout is simulated and the order is marked as paid.

Example (PowerShell):

```powershell
$env:STRIPE_SECRET_KEY="sk_test_..."
python manage.py runserver
```

## Branches

- `feature/diet`: Work on the diet app (diet CRUD, migrations).
- `feature/exercises`: Exercise library improvements and exercise views.
- `feature/store`: Store, cart, and checkout UI/logic work.
- `feature/users`: User profiles, authentication, and account pages.
- `feature/progress`: Progress tracking, entries, and views.
- `refactor/models`: Model refactors and database migrations.
- `docs/update-readme`: Documentation updates (this README section).

PR pages were opened for these branches; visit your repository to create PRs.
