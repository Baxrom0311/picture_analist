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

## Tests

```bash
python manage.py test
# or
pytest
```
