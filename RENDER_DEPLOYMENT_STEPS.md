# Deploy Koki's Foodhub to Render - Step-by-Step Guide

## Prerequisites
- GitHub account with your repository pushed
- Render account (https://render.com)
- Your GitHub repository URL

## Step 1: Push Your Code to GitHub

```powershell
cd c:\Users\Joanna\koki_foodhub3

# Stage all changes
git add .

# Commit your changes
git commit -m "Final dashboard improvements and deployment setup"

# Push to main branch
git push origin main
```

## Step 2: Create Render Account & Connect GitHub

1. Go to https://render.com
2. Sign up or log in
3. Click "New +" → "Web Service"
4. Select "Connect a repository"
5. Search for "koki-foodhub" repository
6. Click "Connect"

## Step 3: Configure Web Service

When creating the service, use these settings:

- **Name**: `koki-foodhub` (or any name you prefer)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Start Command**: `gunicorn koki_foodhub.wsgi`
- **Plan**: Select based on your needs (Free tier available)

## Step 4: Add Environment Variables

In the Render dashboard, add these environment variables:

```
DEBUG=False
SECRET_KEY=<your-secret-key-here>
ALLOWED_HOSTS=<your-render-url>.onrender.com,localhost
DATABASE_URL=<automatically set by Render PostgreSQL>
```

### Get Your Secret Key:
If you don't have a SECRET_KEY, generate one:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 5: Create PostgreSQL Database (if using free tier)

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Set name to `koki-foodhub-db`
3. Region: Choose closest to your location
4. PostgreSQL Version: 15
5. Click "Create Database"

### Connect Database to Web Service:
1. Go to your web service
2. Click "Environment"
3. The `DATABASE_URL` should be auto-populated from the PostgreSQL instance
4. Or manually add it from the database details page

## Step 6: Deploy

1. On the Render dashboard, your web service should start building automatically
2. Watch the deployment logs to ensure everything works
3. Once the "Deploy successful" message appears, your app is live!

## Step 7: Run Initial Setup on Render

After first deploy, run migrations:

```
# In Render dashboard, go to your service → Shell
python manage.py migrate
python manage.py createsuperuser  # Create admin account
```

Or these will run automatically with the `release` command in Procfile.

## Step 8: Access Your Application

Your app will be available at:
```
https://koki-foodhub.onrender.com
```

(Replace with your actual Render domain)

## Troubleshooting

### Build Fails
- Check that all dependencies in `requirements.txt` are installed
- Verify Python version is 3.9+
- Check build logs for specific errors

### Database Connection Issues
- Verify DATABASE_URL is set correctly
- Run migrations: `python manage.py migrate`
- Check database credentials

### Static Files Not Loading
- Ensure `STATIC_URL` is configured in settings.py
- Run: `python manage.py collectstatic --noinput`
- Check CloudFlare/CDN settings if applicable

### Login Issues
- Clear browser cache and cookies
- Verify session settings in settings.py
- Check CSRF configuration

## Important Notes

✅ Your configuration includes:
- Auto migrations on deploy (Procfile)
- Environment-based settings (DEBUG, SECRET_KEY, etc.)
- Static file collection (WhiteNoise)
- PostgreSQL support (psycopg2-binary)
- Gunicorn web server

🔐 Security:
- DEBUG is False in production
- SECRET_KEY is environment variable
- ALLOWED_HOSTS restricted to your domain
- HTTPS auto-enabled by Render

## Next Steps

1. Monitor your app on Render dashboard
2. Check logs regularly for errors
3. Set up monitoring/alerts if needed
4. Configure custom domain if you have one
5. Set up automatic deploys from main branch

## Support

- Render Docs: https://render.com/docs
- Django Docs: https://docs.djangoproject.com/
- PostgreSQL: https://www.postgresql.org/docs/
