# 🚀 Render Deployment - Complete Checklist

## ✅ LOCAL SETUP (Already Done)
- [x] Code committed to GitHub (commit: a1f2715)
- [x] requirements.txt configured with all dependencies
- [x] Procfile created with migration + init commands
- [x] settings.py configured for production
- [x] Database fallback settings (SQLite → PostgreSQL)
- [x] init_render.py management command created (auto-creates admin user)
- [x] .env.example template created

---

## 🔄 RENDER DEPLOYMENT STEPS

### STEP 1: CREATE POSTGRESQL DATABASE ✅
**Status: Check if done**
```
Action Needed:
1. Go to https://render.com/dashboard
2. Click "+ New" → "PostgreSQL"
3. Create database named: koki-foodhub-db
4. Copy the connection string (DATABASE_URL)
```

### STEP 2: CREATE WEB SERVICE ✅
**Status: Already Created (service shows "Deployed")**
```
Confirmed:
✅ Service: koki-foodhub
✅ URL: https://koki-foodhub.onrender.com
✅ Python 3 runtime
✅ GitHub connected
```

### STEP 3: SET ENVIRONMENT VARIABLES ⚠️
**Status: LIKELY MISSING - This is probably why you got 500 error**
```
Action Needed - Go to Render Dashboard:
1. Click "koki-foodhub" web service
2. Click "Environment" tab
3. Add these variables:

   KEY                VALUE
   ─────────────────────────────────────
   DEBUG              False
   SECRET_KEY         [Generate via: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"]
   DATABASE_URL       postgresql://[user]:[password]@[host]:5432/[dbname]
   ALLOWED_HOSTS      koki-foodhub.onrender.com
   ADMIN_EMAIL        admin@koki-foodhub.com
   ADMIN_PASSWORD     [your admin password]

4. Click "Save"
5. Render auto-redeploys
```

### STEP 4: TRIGGER MANUAL DEPLOY ⚠️
**Status: MIGHT NEED TO DO THIS**
```
Action Needed:
1. Go to Render dashboard
2. Click "koki-foodhub" service
3. Click "Manual Deploy" button (or "Deploy latest commit")
4. Watch Logs tab for:
   ✓ Fetching code...
   ✓ Installing dependencies...
   ✓ Running migrations...
   ✓ Creating admin user...
   ✓ Service is live
```

### STEP 5: ACCESS YOUR APP 🎯
**Status: NOT YET (because 500 error)**
```
Once deploy succeeds:
1. Go to: https://koki-foodhub.onrender.com
2. You should see login page (not 500 error)
3. Login with:
   Username: admin
   Password: [your ADMIN_PASSWORD from env vars]
4. Test dashboard features
```

---

## 🔍 WHAT YOU LIKELY MISSED

Based on the 500 error, here's what's probably missing:

### ❌ Missing: DATABASE_URL Environment Variable
```
This is THE MOST COMMON CAUSE of 500 errors
Your app can't connect to PostgreSQL without this
```

### ❌ Missing: SECRET_KEY Environment Variable
```
Django needs this for security - it's required in production
```

### ❌ Missing: Manual Redeploy After Setting Env Vars
```
Setting env vars requires a redeploy to take effect
```

---

## ⚡ QUICK FIX (Do This Now)

1. **Go to**: https://render.com/dashboard
2. **Click**: koki-foodhub service
3. **Click**: Environment tab
4. **Add**:
   ```
   DATABASE_URL = postgresql://[copy from your PostgreSQL database]
   SECRET_KEY = [generate new one]
   DEBUG = False
   ADMIN_PASSWORD = [create a password]
   ```
5. **Click**: Save
6. **Click**: Manual Deploy button
7. **Wait**: 2-5 minutes for build
8. **Check**: Logs for success
9. **Visit**: https://koki-foodhub.onrender.com

---

## 📊 DEPLOYMENT STATUS

| Step | Status | Action |
|------|--------|--------|
| 1. Code on GitHub | ✅ Done | None |
| 2. Web Service Created | ✅ Done | None |
| 3. PostgreSQL Database | ⚠️ Verify | Check if created |
| 4. Environment Variables | ❌ MISSING | **DO THIS NOW** |
| 5. Manual Deploy | ❌ MISSING | **DO THIS AFTER #4** |
| 6. Test App | ⏳ Pending | After successful deploy |

---

## 🆘 IF YOU STILL GET 500 ERROR

Send me:
1. Screenshot of your Render **Logs** tab
2. Screenshot of your Render **Environment** tab
3. Your **PostgreSQL connection string** (from database settings)

Then I can debug the exact issue! 🔍

---

## ✨ ONCE IT WORKS

Your live app will have:
- ✅ Login & user authentication
- ✅ Product dashboard
- ✅ Shopping cart
- ✅ Payment processing
- ✅ Sales reports
- ✅ Admin panel at /admin
- ✅ All features from local development
