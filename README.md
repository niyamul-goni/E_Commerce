# E-Commerce Management System

Full-stack e-commerce assignment scaffold built with React, FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT auth, and bcrypt hashing. The backend now also supports running against a Supabase-hosted Postgres database.

## Completed So Far

- Backend project structure under `backend/`
- Normalized SQLAlchemy models for all core tables
- FastAPI app entrypoint and CORS setup
- JWT/password helper utilities
- Alembic migration wiring
- CRUD and route modules for auth, catalog, commerce, and dashboard endpoints
- PostgreSQL schema script in `database/schema.sql`
- Sample seed data in `database/seed.sql`
- SQL concept demo queries in `docs/sql_concepts.sql`
- API example notes in `docs/api_examples.md`

## Folder Structure

- `backend/` FastAPI app, Alembic, and Python dependencies
- `frontend/` React app scaffold with routing, cart, checkout, orders, reviews, and admin pages
- `database/` SQL schema and seed scripts
- `docs/` API and SQL demo notes

## Backend Setup

1. Create a virtual environment inside `backend/`
2. Install dependencies from `backend/requirements.txt`
3. Copy `backend/.env.example` to `backend/.env`
4. Update `SUPABASE_DATABASE_URL` or `DATABASE_URL`, `SECRET_KEY`, and CORS origins
5. Run the PostgreSQL schema or let Alembic create tables

If you are moving to Supabase, also set `SUPABASE_URL` and the keys you plan to use for auth or storage. The `SUPABASE_URL` project URL is not the same as the database connection string, so SQLAlchemy still needs `SUPABASE_DATABASE_URL` or `DATABASE_URL`.

### Product images on multiple computers

Manager uploads use Supabase Storage automatically when `SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_STORAGE_BUCKET` are configured.
The backend creates the public `product-images` bucket on the first upload if
it does not exist. This keeps newly uploaded images available to every teammate
and deployment instead of saving them on only one computer.

Use `PRODUCT_IMAGE_STORAGE=local` only for offline development. Local uploads
are written to `backend/static/products` and must be committed separately if
another clone needs them. Never commit `backend/.env` or the service role key.

## Database

You can initialize the database with either:

- `database/schema.sql` for direct SQL execution, or
- Alembic migrations once the first revision is generated

Then load sample data from `database/seed.sql`.

## Current API Surface

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/products`
- `GET /api/v1/products/search`
- `GET /api/v1/orders/me`
- `POST /api/v1/orders`
- `POST /api/v1/payments`
- `POST /api/v1/shipments`
- `POST /api/v1/reviews`
- `GET /api/v1/dashboard/summary`

## Frontend

The React frontend is implemented under `frontend/` with React Router, axios-based API integration, reusable components, validation, loading states, and admin management pages. If you later switch auth/storage to Supabase, the frontend already has placeholder environment variables for the project URL and anon key.
