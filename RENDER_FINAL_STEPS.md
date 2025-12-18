# 🚀 Render Deployment Checklist for Koki's Foodhub

Your code is now live on GitHub at: https://github.com/jhoanabenedicto3-ai/koki-foodhub

## ✅ Pre-Deployment Verification

Your project has:
- ✅ Django 5.2.6 configured for production
- ✅ PostgreSQL database support
- ✅ Gunicorn web server
- ✅ WhiteNoise for static files
- ✅ Procfile with migrations
- ✅ requirements.txt with all dependencies
- ✅ runtime.txt with Python 3.11.7
- ✅ Production settings configured

## 📋 Step-by-Step Deployment on Render

### Step 1: Create PostgreSQL Database (5 minutes)

1. Go to: https://dashboard.render.com
2. Click **"New"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `koki-foodhub-db`
   - **Database:** `koki_foodhub`
   - **User:** `koki_user`
   - **Region:** Choose your closest location
   - **PostgreSQL Version:** 15
4. Click **"Create Database"**
5. **Copy and save these from the connection string:**
   - `POSTGRES_HOST` (looks like: `dpg-xxx.render.com`)
   - `POSTGRES_PASSWORD`

### Step 2: Create Web Service (10 minutes)

1. Go to: https://dashboard.render.com
2. Click **"New"** → **"Web Service"**
3. Select **"Deploy existing code from a repository"**
4. Authorize Render to access GitHub if prompted
5. Select: `jhoanabenedicto3-ai/koki-foodhub`
6. Click **"Connect"**

### Step 3: Configure Web Service Settings

Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `koki-foodhub` |
| **Region** | Same as your database |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn koki_foodhub.wsgi` |

### Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** and add these:

```
DEBUG=False
ALLOWED_HOSTS=koki-foodhub.onrender.com

POSTGRES_NAME=koki_foodhub
POSTGRES_USER=admin
POSTGRES_PASSWORD=[paste from database connection string]
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

**To generate SECRET_KEY:**

Open PowerShell and run:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then add as environment variable:
```
SECRET_KEY=[paste the generated key]
```

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (usually 3-5 minutes)
3. Watch the "Logs" tab for:
   - `Collecting` - installing dependencies
   - `Collecting static files` - assets
   - `Running migrations` - database setup
4. Once successful, you'll see: `"Successfully collected 1 static files"`

### Step 6: Access Your App

1. Your app URL will be: `https://koki-foodhub.onrender.com`
2. Click the URL or check the dashboard for the exact URL

## 📊 Post-Deployment Tasks

### Create Superuser

1. In Render Web Service, click **"Shell"**
2. Run: `python manage.py createsuperuser`
3. Follow the prompts
4. Login at: `https://your-app.onrender.com/admin`

### Test the Application

- Navigate to dashboard
- Try searching for products
- Test the transaction cart
- Check admin panel

## 🔄 Future Updates

After making changes locally:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Render automatically redeploys when you push!

## 🆘 Troubleshooting

### Build Fails
- Check "Logs" tab for specific error
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### Database Connection Error
- Double-check `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Verify PostgreSQL service is running
- Check if database name is `koki_foodhub` (case-sensitive)

### App shows 500 Error
- Check "Logs" for detailed error message
- Run locally: `python manage.py check`
- Verify migrations ran: Check Logs for "Running migrations"

### Static Files Not Loading
- Confirm `collectstatic` ran (should see "collected X static files")
- Check WhiteNoise is in MIDDLEWARE
- Visit `/static/` URL to test

## 📞 Support Links

- [Render Django Docs](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [WhiteNoise Setup](https://whitenoise.readthedocs.io/)

---

**You're ready to deploy! Follow the steps above and your app will be live in ~15 minutes.** 🚀
