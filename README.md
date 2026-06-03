# Final-Project---Team-Codex

Fitness Hub - Django Fitness Platform by Team

Quick start:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

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
