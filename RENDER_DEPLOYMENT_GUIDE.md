# Render Deployment Guide for Koki's Foodhub

## Prerequisites
- GitHub account
- Render.com account (https://render.com)
- Your project is ready to deploy

## Step 1: Push to GitHub

1. **Create a new GitHub repository:**
   - Go to https://github.com/new
   - Repository name: `koki-foodhub` (or your preferred name)
   - Choose Public or Private
   - Click "Create repository"

2. **Add remote and push code:**
   ```bash
   cd C:\Users\Joanna\koki_foodhub3
   git remote add origin https://github.com/jhoanabenedicto3-ai/koki-foodhub.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Create PostgreSQL Database on Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click "New" → "PostgreSQL"

2. **Configure PostgreSQL:**
   - **Name:** `koki-foodhub-db` (or your choice)
   - **Database:** `koki_foodhub`
   - **User:** `koki_user`
   - **Region:** Select closest to your location
   - **PostgreSQL Version:** 15
   - Click "Create Database"

3. **Save Connection Details:**
   - After creation, you'll see a connection string
   - Save it somewhere safe - you'll need it in the next step

## Step 3: Create Web Service on Render

1. **Create New Web Service:**
   - Go to https://dashboard.render.com
   - Click "New" → "Web Service"
   - Select "Deploy existing code from a repository"

2. **Connect GitHub Repository:**
   - Authorize Render to access your GitHub
   - Select your `koki-foodhub` repository
   - Click "Connect"

3. **Configure Web Service:**
   - **Name:** `koki-foodhub` (or your choice)
   - **Region:** Same as your database
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn koki_foodhub.wsgi`

4. **Add Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Add the following variables:

   ```
   DEBUG = False
   ALLOWED_HOSTS = your-app-name.onrender.com,www.your-app-name.onrender.com
   SECRET_KEY = generate-a-new-secret-key-here
   
   POSTGRES_NAME = koki_foodhub
   POSTGRES_USER = koki_user
   POSTGRES_PASSWORD = [from your database connection string]
   POSTGRES_HOST = [from your database connection string]
   POSTGRES_PORT = 5432
   ```

   **To generate SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Configure Database Connection String:**
   - From your Render PostgreSQL database page, copy the "Internal Database URL"
   - Or manually use: `postgresql://username:password@host:port/database`

## Step 4: Deploy

1. **Click "Create Web Service"**
   - Render will automatically start building and deploying
   - Wait for the deployment to complete (usually 3-5 minutes)

2. **Monitor Logs:**
   - Go to your Web Service's "Logs" tab
   - Watch for migration and collectstatic messages

3. **Access Your App:**
   - Once deployed, you'll see a live URL (e.g., `https://koki-foodhub-xxxx.onrender.com`)
   - Click the URL to access your app

## Step 5: Database Migrations

The database migrations should run automatically via the `release` command in your Procfile.

If you need to run migrations manually:

1. **Use Render Shell:**
   - Go to your Web Service
   - Click "Shell" tab
   - Run: `python manage.py migrate`

2. **Create Superuser (optional):**
   - In the Shell: `python manage.py createsuperuser`
   - Follow the prompts

## Important Environment Variables Explained

- **DEBUG:** Set to `False` for production
- **ALLOWED_HOSTS:** List of domains that can access your app
- **SECRET_KEY:** Keep this secret! Generate a new one for production
- **POSTGRES_* vars:** Database connection details
- **CSRF_TRUSTED_ORIGINS:** Add if using a custom domain

## Troubleshooting

### Build Fails
- Check the "Logs" tab for error messages
- Common issues:
  - Missing dependencies in `requirements.txt`
  - Database connection errors
  - Invalid environment variables

### Database Connection Error
- Verify PostgreSQL is running on Render
- Check `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Ensure database name matches

### App Shows 500 Error
- Check "Logs" for detailed error messages
- Run `python manage.py check` locally to verify settings
- Ensure migrations ran successfully

### Static Files Not Loading
- Verify `STATIC_ROOT` and `STATIC_URL` in settings
- Check that `python manage.py collectstatic` ran during build
- Ensure WhiteNoise middleware is installed

## Domain Management (Optional)

To use a custom domain:

1. **Add Custom Domain:**
   - Go to Web Service Settings
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `koki-foodhub.com`)

2. **Update DNS Records:**
   - Add CNAME record pointing to Render's domain
   - DNS provider will have specific instructions

## Updating Your App

After making changes:

1. **Commit and push to GitHub:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

2. **Render automatically redeploys** when you push to the main branch

## Additional Resources

- [Render Django Deployment Guide](https://render.com/docs/deploy-django)
- [Django Production Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [WhiteNoise Documentation](https://whitenoise.readthedocs.io/)

---

**Deployment Complete!** 🎉 Your Koki's Foodhub system is now live on Render.
