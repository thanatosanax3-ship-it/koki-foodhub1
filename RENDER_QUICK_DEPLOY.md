# 🚀 Render Deployment Quick Start - Koki's Foodhub

## ✅ What's Ready for Deployment

Your application is fully configured for Render deployment with:

- ✅ **Django 5.2.6** with production settings
- ✅ **PostgreSQL Support** (psycopg2-binary)
- ✅ **Gunicorn Web Server** configured
- ✅ **WhiteNoise** for static files in production
- ✅ **Environment-based configuration** (DEBUG, SECRET_KEY, ALLOWED_HOSTS)
- ✅ **Database migrations** via Procfile release command
- ✅ **render.yaml** blueprint for one-click deployment

## 📋 Deployment Steps (2 minutes to live!)

### Step 1: Go to Render Dashboard
https://render.com

### Step 2: Connect GitHub Repository
1. Click **"New +"** → **"Web Service"**
2. Select **"Deploy an existing repository"**
3. Find **"koki-foodhub"** repository
4. Click **"Connect"**

### Step 3: Configure Service
The form should auto-populate from render.yaml, but verify:

| Setting | Value |
|---------|-------|
| **Name** | `koki-foodhub` (or your choice) |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn koki_foodhub.wsgi` |
| **Plan** | Free (or Starter) |

### Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** for each:

```
DEBUG = False
SECRET_KEY = (generate one below)
ALLOWED_HOSTS = <your-app>.onrender.com
```

#### Generate Secret Key (run locally):
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Create Database
1. Click **"New +"** → **"PostgreSQL"**
2. Set **Name** to: `koki-foodhub-db`
3. Region: Choose closest to your users
4. Click **"Create Database"**

### Step 6: Connect Database to Web Service
1. Go back to your **Web Service**
2. Click **"Environment"** tab
3. Add **`DATABASE_URL`** environment variable
4. Get the URL from PostgreSQL instance details page
5. Click **"Save"**

### Step 7: Deploy
1. Click **"Create Web Service"**
2. Watch the build logs - should complete in 2-5 minutes
3. Look for: **"✓ Deploy successful"**

### Step 8: Initialize Database
After deployment, run migrations:

```
In Render Dashboard → Your Web Service → "Shell" tab

$ python manage.py migrate
$ python manage.py createsuperuser
```

(Or these run automatically from Procfile `release` command)

## 🌐 Your Live App URL

After deployment, access your app at:
```
https://koki-foodhub.onrender.com
```

(Render will provide your exact URL)

---

## ⚠️ Important Reminders

### Environment Variables
- `DEBUG` must be `False` in production
- `SECRET_KEY` must be random and secret (never commit it!)
- `ALLOWED_HOSTS` must include your Render domain

### Database
- Render PostgreSQL is included with Blueprint
- Automatic daily backups enabled
- Connection pooling configured

### Static Files
- WhiteNoise handles static files in production
- Run `collectstatic` during build (automatic)
- CSS/JS served from `/static/` path

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check build logs, verify requirements.txt |
| 404 errors | Run migrations, check ALLOWED_HOSTS |
| Static files missing | Ensure collectstatic ran successfully |
| Database connection error | Verify DATABASE_URL is set correctly |
| Login not working | Clear cookies, check CSRF settings |

---

## 📊 Deployment Features

Your app includes:

✅ **Product Management**
- Product search and filtering by category
- Size selection (Regular, Medium, Large, XL, XXL)
- Auto price adjustments based on size

✅ **Shopping Cart**
- Add/remove items with quantity controls
- Real-time total and change calculation
- Size-specific cart items

✅ **Payment Processing**
- Accept cash payments
- Generate sales records
- Persist to localStorage

✅ **Sales Dashboard**
- View today's sales
- Weekly/monthly reports
- Product breakdown by revenue

✅ **Reporting**
- Print sales reports with statistics
- Product breakdown table
- Auto-format for printing

---

## 🛠️ Production Checklist

- [ ] Environment variables set correctly
- [ ] Database connected and migrated
- [ ] SECRET_KEY is random and secret
- [ ] DEBUG is False
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Static files loading correctly
- [ ] Admin user created
- [ ] Test payment processing
- [ ] Test login/logout
- [ ] Check error logs

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.2/howto/deployment/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Gunicorn**: https://gunicorn.org/

---

## 🎉 You're Ready!

Your Koki's Foodhub application is ready for production on Render.
Follow the 8 steps above and you'll be live in minutes!

Good luck! 🚀
