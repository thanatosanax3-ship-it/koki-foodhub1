# 🔧 Render PostgreSQL Configuration Guide

Your PostgreSQL database is ready! Now you need to add the connection details to your Render Web Service.

## 📋 Step 1: Get Your Database Connection String

1. Go to https://dashboard.render.com
2. Click on your PostgreSQL database (it should be listed under your services)
3. Look for the **"Connections"** section
4. Copy the **"Internal Database URL"** - it looks like:
   ```
   postgresql://username:password@host.render.com:5432/database_name
   ```

## 🔐 Step 2: Extract Connection Details

From that URL, you need:
- **POSTGRES_NAME** = database_name (the part after the last `/`)
- **POSTGRES_USER** = username (the part before the `:`)
- **POSTGRES_PASSWORD** = password (the part after the `:` and before the `@`)
- **POSTGRES_HOST** = host.render.com (the part after the `@` and before the `:5432`)
- **POSTGRES_PORT** = 5432

**Example:**
If your URL is: `postgresql://koki_user:abc123xyz@dpg-xyz.render.com:5432/koki_foodhub`

Then your variables are:
POSTGRES_USER = `koki_user`
POSTGRES_PASSWORD = `abc123xyz`
POSTGRES_HOST = `dpg-xyz.render.com`
POSTGRES_NAME = `koki_foodhub`
POSTGRES_PORT = `5432`

## 🌐 Step 3: Add Environment Variables to Web Service

1. Go to https://dashboard.render.com
2. Click on your **Web Service** (koki-foodhub)
3. Click **"Environment"** in the left menu
4. Click **"Add Environment Variable"** for each:

```
DEBUG=False
ALLOWED_HOSTS=koki-foodhub.onrender.com

POSTGRES_NAME=koki_foodhub
POSTGRES_USER=koki_user
POSTGRES_PASSWORD=[your password]
POSTGRES_HOST=[your host]
POSTGRES_PORT=5432
```

**For SECRET_KEY, generate a new one:**
Open PowerShell and run:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then add:
```
SECRET_KEY=[paste the generated key]
```

## 🔄 Step 4: Redeploy Web Service

After adding all environment variables:

1. Click **"Manual Deploy"** → **"Deploy latest commit"**
   OR
2. Go to **"Settings"** → **"Auto-Deploy"** and trigger a new deploy

Wait 3-5 minutes for deployment to complete.

## ✅ Step 5: Verify Connection

Once deployed:
1. Open your app: https://koki-foodhub.onrender.com
2. Click **"Shell"** on your Web Service dashboard
3. Run: `python manage.py dbshell`
4. If it connects without error, your database is working! ✅

## 🆘 If Still Having Issues

**Check the logs:**
1. Go to your Web Service
2. Click **"Logs"** tab
3. Look for database connection errors
4. Verify all POSTGRES_* variables are correct

**Common issues:**
- ❌ Wrong POSTGRES_PASSWORD
- ❌ Wrong POSTGRES_HOST
- ❌ POSTGRES_NAME doesn't exist in database
- ❌ Missing POSTGRES_PORT (must be 5432)

---

**Once configured, your app will be fully functional!** 🚀
