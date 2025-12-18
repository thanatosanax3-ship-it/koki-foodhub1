# Deploying to Render — Checklist

This document lists the steps to deploy the `koki-foodhub` Django app to Render.

Prerequisites
- A Git repository (this repo) pushed to GitHub or GitLab.
- A Render account with access to create web services and databases.

1) Commit & push your code

```powershell
git add -A
git commit -m "Prepare app for Render deployment: render.yaml + settings"
git push origin main
```

2) Add a managed Postgres on Render
- In Render: New → Database → Postgres
- Choose a plan (Starter is fine for small deployments).
- After creation, either attach the DB to your web service later or copy the `DATABASE_URL`.

3) Create the Web Service
- In Render: New → Web Service → Connect your repo
- Branch: `main`
- Environment: `Python`
- Start command: leave blank to use `Procfile` (we have `web: gunicorn koki_foodhub.wsgi`) or set to `gunicorn koki_foodhub.wsgi`
- Build command: leave blank (Render defaults) or set to:
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```

4) Environment variables (Render service settings)
- `SECRET_KEY` — set to a secure random value (mark as a secret on Render)
- `DEBUG` — `False`
- `ALLOWED_HOSTS` — comma-separated host(s) (e.g. `your-service.onrender.com`)
- If using Render-managed Postgres, `DATABASE_URL` will be supplied automatically when the DB is attached. Otherwise set one of:
  - `POSTGRES_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

5) Release / Migrations
- Our `Procfile` includes a `release` entry: `release: python manage.py migrate` — Render will run this automatically on deploy if you leave the release command enabled.

6) Static files
- `collectstatic` runs in the build step above. We use WhiteNoise for static serving in production.

7) After deploy
- Verify the service logs in Render (Deploy → Events & Logs)
- Visit the site over HTTPS (Render provides TLS)
- If you see template errors about missing env vars, add them in the Render dashboard and redeploy.

Optional: render.yaml
- This repo includes `render.yaml` that declares a web service and a managed Postgres. Review it and adjust `plan`, `envVars`, and secret references before using.

Security notes
- Do NOT commit production secret keys into the repository. Use Render's secret/env-vars panel.
- For media uploads consider S3 or another external object store for persistence.

Support
- If you want, I can walk you through the Render UI fields while you create the service — tell me which step you want help with and I'll provide exact values to paste.
