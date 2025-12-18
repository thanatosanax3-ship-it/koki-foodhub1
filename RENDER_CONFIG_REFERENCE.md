# Render Deployment Configuration Reference

## Your render.yaml Blueprint

```yaml
services:
  - type: web
    name: koki-foodhub-web
    env: python
    branch: main
    plan: free
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: gunicorn koki_foodhub.wsgi
    envVars:
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        value: "@secret_key"
databases:
  - name: koki-foodhub-db
    plan: starter
```

## Environment Variables Reference

### Required
- `SECRET_KEY`: Django secret key (generate with manage.py)
- `DEBUG`: Must be "False" for production
- `ALLOWED_HOSTS`: Your Render domain (e.g., koki-foodhub.onrender.com)
- `DATABASE_URL`: Auto-set by Render PostgreSQL (format: postgresql://...)

### Optional
- `POSTGRES_NAME`: Database name (default: postgres)
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port (default: 5432)

## Settings.py Highlights

### Database Configuration
```python
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Parse DATABASE_URL from Render
    from urllib.parse import urlparse
    url = urlparse(DATABASE_URL)
    db_name = url.path[1:]
    db_user = url.username
    db_password = url.password
    db_host = url.hostname
    db_port = url.port
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port or '5432',
        }
    }
```

### Static Files
```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for production static file serving
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Security
```python
DEBUG = os.getenv("DEBUG", "False") == "True"  # False in production
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-key-change-in-production")
```

## Procfile

```
release: python manage.py migrate
web: gunicorn koki_foodhub.wsgi
```

The `release` command runs migrations automatically before each deploy.

## requirements.txt

All production dependencies:
```
Django==5.2.6
psycopg2-binary==2.9.10
python-dotenv==1.0.0
gunicorn==22.0.0
whitenoise==6.6.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

## Render Build Process

1. **Install Dependencies** (buildCommand)
   ```
   pip install -r requirements.txt
   ```

2. **Collect Static Files** (buildCommand)
   ```
   python manage.py collectstatic --noinput
   ```

3. **Run Release Command** (Procfile)
   ```
   python manage.py migrate
   ```

4. **Start Web Server** (startCommand)
   ```
   gunicorn koki_foodhub.wsgi
   ```

## Common Environment Variable Values

### For Render Deployment
```
DEBUG=False
SECRET_KEY=YOUR_RANDOM_SECRET_KEY_HERE
ALLOWED_HOSTS=koki-foodhub.onrender.com,localhost
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

### To Generate SECRET_KEY
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Deployment Checklist

### Before Deployment
- [ ] All code committed and pushed to main branch
- [ ] requirements.txt up to date
- [ ] Static files configured (STATIC_ROOT, STATICFILES_DIRS)
- [ ] Database settings support PostgreSQL
- [ ] SECRET_KEY generated and ready
- [ ] DEBUG is False for production
- [ ] ALLOWED_HOSTS configured

### After Deployment
- [ ] Service building without errors
- [ ] Database connected and migrated
- [ ] Admin user created
- [ ] Static files loading (CSS, images)
- [ ] Authentication working
- [ ] Payment processing functional
- [ ] Reports generating and printing
- [ ] Error logs clean

## Debugging on Render

### View Logs
1. Go to your service on Render
2. Click "Logs" tab
3. Search for errors or "ERROR", "CRITICAL"

### Access Shell
1. Go to your service
2. Click "Shell" tab
3. Run Django commands:
   ```
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py shell
   ```

### Common Issues & Solutions

**502 Bad Gateway**
- Check web server logs
- Verify SECRET_KEY is set
- Confirm database connection

**Static files not loading (404)**
- Verify collectstatic ran successfully
- Check STATIC_ROOT path
- Ensure WhiteNoise middleware is present

**Database connection refused**
- Verify DATABASE_URL is set
- Check PostgreSQL instance is running
- Confirm credentials in DATABASE_URL

**Import errors on deploy**
- Check requirements.txt has all packages
- Verify Python version compatibility
- Look for typos in package names

## Monitoring & Maintenance

### Enable Monitoring
- Render dashboard shows CPU, memory, bandwidth
- Email alerts for deployment failures
- Auto-restart on crashes

### Database Backups
- Render provides daily automatic backups
- Access backups in PostgreSQL instance settings
- Manual backups can be created anytime

### Scaling
- Free plan: 0.5 CPU, 512MB RAM
- Starter plan: better performance, hourly backups
- Professional plan: custom resources, 24/7 support

## More Resources

- Render Django Guide: https://render.com/docs/deploy-django
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/
- WhiteNoise: https://whitenoise.readthedocs.io/
- Gunicorn: https://gunicorn.org/

---

**Your app is ready for production! Deploy with confidence.** 🚀
