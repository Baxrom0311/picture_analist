# 🎨 AI Art Evaluation System

AI-powered art evaluation system using **Google Gemini LLM**. Evaluates artwork across 5 categories with weighted scoring.

## Quick Start

```bash
# 1. Virtual environment
# Recommended runtime: Python 3.12
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
# For Supabase/hosted Postgres, set DATABASE_URL instead of DB_* variables
# Optional: set ADMIN_URL=analyst/ if you want the Django admin at /analyst/
# Optional for shared admin hosts: set STATIC_URL=/analyst-static/ and MEDIA_URL=/analyst-media/

# 4. Database setup
python manage.py makemigrations
python manage.py migrate

# 5. Load categories
python manage.py loaddata fixtures/categories.json

# 6. Create superuser
python manage.py createsuperuser

# 7. Run server
python manage.py runserver
```

## API Endpoints (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register |
| POST | `/api/v1/auth/login/` | Login (JWT) |
| POST | `/api/v1/auth/refresh/` | Refresh token |
| POST | `/api/v1/auth/logout/` | Logout |
| GET | `/api/v1/auth/profile/` | Profile |
| GET | `/api/v1/auth/profile/stats/` | Stats |
| GET/POST | `/api/v1/artworks/` | List/Upload |
| GET/PUT/DELETE | `/api/v1/artworks/{id}/` | Detail |
| POST | `/api/v1/artworks/{id}/re-evaluate/` | Re-evaluate |
| GET | `/api/v1/evaluations/` | List evaluations |
| GET | `/api/v1/evaluations/{id}/` | Evaluation detail |
| GET | `/api/v1/categories/` | List categories |

## 📚 API Documentation

The API Documentation is available in the following formats:

- **Swagger UI**: [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/) - Interactive API testing
- **ReDoc**: [http://localhost:8000/api/v1/redoc/](http://localhost:8000/api/v1/redoc/) - Clean, structured documentation
- **OpenAPI Schema**: [http://localhost:8000/api/v1/schema/](http://localhost:8000/api/v1/schema/) - Raw YAML/JSON schema

### Test Credentials
- **Username**: `admin`
- **Password**: `admin123` (Change this in production!)

## Docker

```bash
docker-compose up -d
```

## Tech Stack

- Django 4.2 + DRF
- PostgreSQL / SQLite
- Redis + Celery
- Google Gemini API (via `google-genai` SDK)
- JWT Authentication

## Supabase Postgres

If you deploy with Supabase, copy the Postgres connection string from the Supabase project dashboard and set it as `DATABASE_URL`.

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
```

The app now supports `DATABASE_URL` directly in both development and production settings, so you do not need to split the connection into `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

## Render Deploy

This repo now includes [`render.yaml`](./render.yaml) for a free Render web service deploy.

Recommended environment values on Render:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=replace-this-with-a-random-secret
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-...pooler.supabase.com:5432/postgres?sslmode=require
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.vercel.app
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
CELERY_TASK_ALWAYS_EAGER=True
SERVE_MEDIA=True
```

`ALLOWED_HOSTS` does not need the default Render hostname because Render sets `RENDER_EXTERNAL_HOSTNAME` automatically. Add `ALLOWED_HOSTS` only if you later attach a custom domain.

Free Render caveats:

- `CELERY_TASK_ALWAYS_EAGER=True` runs evaluations inside the web request. This is fine for demos, but slow requests can still time out.
- `SERVE_MEDIA=True` makes Django serve uploaded files directly. This works for hobby deploys, but Render free disks are ephemeral, so uploaded files can disappear after restart or redeploy.
- For durable uploads, move media to S3-compatible storage later.

## Tests

```bash
python manage.py test
# or
pytest
```
