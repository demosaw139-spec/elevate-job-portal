# Elevate

Elevate is a Django job-portal starter focused on the essential end-to-end workflow: candidates discover and save published roles, submit applications, and track their status; employers maintain a company profile, publish roles, and update applicants. The app includes a responsive navy-and-gold interface, a lightweight Three.js hero enhancement with a CSS fallback, Django session authentication, a browsable REST API, and Django's permission-protected administration site.

The broader product brief includes many additional modules (verification and recovery emails, document uploads, advanced ATS, editorial content, billing, analytics, recommendations, and moderation workflows). Those are not represented as implemented in this starter.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`
- SQLite for local development; PostgreSQL can be selected with the environment variables below.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. The admin interface is at `/admin/`; the REST API is browsable at `/api/jobs/` and `/api/applications/`.

Registration creates either a candidate account or an employer account with a company profile. For a useful demo, create an employer account, publish a role from its dashboard, then create a candidate account and apply.

## Configuration

Copy `.env.example` to `.env` and provide values in your process environment (Django does not load `.env` files automatically). Always set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and a restrictive `DJANGO_ALLOWED_HOSTS` in deployment. Set all `POSTGRES_*` variables to select PostgreSQL; otherwise SQLite is used. Password reset emails print to the development console by default.

Set `DJANGO_DEBUG=False` only behind HTTPS; production mode enables secure cookies and HTTPS redirects. Serve collected static assets with the deployment's static-file server or a CDN.

## Tests

```powershell
python manage.py test portal
```

The tests exercise search, registration, duplicate-application prevention, applicant status changes, employer job ownership, and API permissions.
