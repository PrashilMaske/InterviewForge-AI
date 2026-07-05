# Production Deployment Guide - Render

This guide outlines instructions for deploying InterviewForge AI onto Render. It details deploying the Django web application service, database, background worker, and external static storage integrations.

---

## 1. Required Cloud Resources

Deploying the platform requires three instances on Render:
1. **PostgreSQL Database**: Managed relational database store.
2. **Web Service**: Runs the Django web application (Gunicorn) to serve HTML templates and handles client APIs.
3. **Background Worker**: Runs the Django Q2 cluster to process async resume parsing, JD matching, and PDF exports.

---

## 2. Environment Variables Checklist

Set these variables in a Shared Group on Render to share configs between the Web Service and Background Worker:

| Key | Example Value | Description |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `core.settings` | Standard Django settings module pathway |
| `SECRET_KEY` | `super-secret-production-hash` | Django production secret key |
| `DEBUG` | `False` | Must be False in production |
| `DATABASE_URL` | `postgres://user:password@hostname:5432/db` | Provided automatically by Render PostgreSQL |
| `GROQ_API_KEY` | `gsk_xyz123...` | Groq console developer token |
| `CLOUDINARY_URL` | `cloudinary://api_key:api_sec@cloud_name` | Cloudinary integration endpoint |
| `PORT` | `8000` | Target port for web Gunicorn instances |

---

## 3. Deployment Steps on Render

### Step A: Deploy PostgreSQL Database
1. Go to the Render Dashboard -> click **New** -> Select **PostgreSQL**.
2. Set Name: `interview-forge-db`.
3. Choose Tier (Free / Starter).
4. Click **Create Database**.

### Step B: Setup Web Service
1. Click **New** -> Select **Web Service**.
2. Connect your Git repository.
3. Set configuration fields:
   * **Name**: `interview-forge-web`
   * **Environment**: `Python`
   * **Build Command**:
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_sm && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   * **Start Command**:
     ```bash
     gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3
     ```
4. Attach the Shared Environment Variables Group created earlier.
5. Click **Deploy Web Service**.

### Step C: Setup Background Worker Service
1. Click **New** -> Select **Background Worker**.
2. Connect the same Git repository.
3. Set configuration fields:
   * **Name**: `interview-forge-worker`
   * **Environment**: `Python`
   * **Build Command**:
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   * **Start Command**:
     ```bash
     python manage.py qcluster
     ```
4. Attach the Shared Environment Variables Group.
5. Click **Deploy Background Worker**.

---

## 4. Media and Static Assets Storage (Cloudinary & Whitenoise)

* **Static Assets**:
  CSS, JS, and image elements are served directly by Django's Web Service using `whitenoise` middleware:
  ```python
  MIDDLEWARE = [
      "django.middleware.security.SecurityMiddleware",
      "whitenoise.middleware.WhiteNoiseMiddleware", # Placed right after security
      ...
  ]
  STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
  ```
* **Media Uploads (Resumes & Reports)**:
  Resumes and compiled PDF reports are uploaded directly to Cloudinary using `django-cloudinary-storage` to ensure persistent file storage across stateless dynos.
  ```python
  DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
  ```
