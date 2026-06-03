# Changelog

## Completed (2026-06-03)

Summary: Full implementation of core Fitness Hub features, CRUD flows, store cart and checkout simulation, profile management, dashboard skeleton, tests, and CI.

- Added models and admin registrations:
  - `users.Profile` auto-created on user signup.
  - `exercises.Exercise` (exercise library).
  - `goals.Goal` (user goal planner).
  - `diet.NutritionRecord` (diet entries).
  - `progress.ProgressRecord` (progress entries).
  - `store.Product`, `Cart`, `Order`, `OrderItem` (store models).

- Implemented forms, views, templates, and URLs for:
  - User registration, login, profile view/edit.
  - Dashboard page with a sample Chart.js chart.
  - Goals: list and create (forms + templates).
  - Diet: create/list/edit/delete.
  - Progress: create/list/edit/delete.
  - Exercises: list and detail pages.
  - Store: product list/detail, quick add-to-cart, cart (session-based), update/remove, checkout simulation.

- UX and frontend:
  - Responsive layout and improved navbar per role (public vs authenticated).
  - CSS improvements (`static/css/style.css`) for accessibility, focus states, and responsive grids.
  - JS menu toggle for mobile nav.

- Testing & CI:
  - Unit tests for Goals, Diet, Progress, and Store (8 tests) — all pass locally.
  - GitHub Actions workflow added at `.github/workflows/ci.yml` to run migrations and tests on push/PR.

- Project maintenance:
  - `README.md` updated with setup and CI instructions.
  - `CHANGELOG.md` added (this file).

## Notes & Next Steps

- Add more unit tests and edge-case coverage.
- Implement payment integration (Stripe test mode) for checkout.
- Add user notifications (email, in-app) and better error handling.
- Polish UI and accessibility across all pages.
- Add continuous deployment if desired.

If you want, I can now push this branch to remote, integrate Stripe test payments, or expand tests and CI badges.
