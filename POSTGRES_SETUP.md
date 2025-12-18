# PostgreSQL Migration Guide

## Step 1: Install PostgreSQL (if not already installed)

Download and install PostgreSQL from: https://www.postgresql.org/download/

During installation:
- Remember your superuser password
- Keep default port as 5432

## Step 2: Create PostgreSQL Database

Open PowerShell as Administrator and run:

```powershell
# Connect to PostgreSQL
psql -U postgres

# Then in the PostgreSQL prompt, create the database:
CREATE DATABASE koki_foodhub;
CREATE USER koki_user WITH PASSWORD 'your_password_here';
ALTER ROLE koki_user SET client_encoding TO 'utf8';
ALTER ROLE koki_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE koki_user SET default_transaction_deferrable TO on;
ALTER ROLE koki_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE koki_foodhub TO koki_user;
\q
```

## Step 3: Set Environment Variables

Create a `.env` file in the project root (c:\Users\Joanna\koki_foodhub3\.env):

```
POSTGRES_NAME=koki_foodhub
POSTGRES_USER=koki_user
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Or set them in PowerShell:

```powershell
$env:POSTGRES_NAME="koki_foodhub"
$env:POSTGRES_USER="koki_user"
$env:POSTGRES_PASSWORD="your_password_here"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
```

## Step 4: Run Migrations

```powershell
cd c:\Users\Joanna\koki_foodhub3
python manage.py migrate
```

## Step 5: Create a Superuser (Optional)

```powershell
python manage.py createsuperuser
```

## Step 6: Test Connection

```powershell
python manage.py runserver
```

Visit http://localhost:8000 to test the application.

---

## Optional: Backup SQLite Data

If you want to migrate existing data from SQLite to PostgreSQL:

```powershell
# Dump data from SQLite
python manage.py dumpdata > data.json

# After migration, load data into PostgreSQL
python manage.py loaddata data.json
```

## Troubleshooting

- **psycopg2 error**: Make sure `psycopg2-binary` is installed (already done)
- **Connection refused**: Ensure PostgreSQL server is running
- **Wrong password**: Check your credentials in environment variables
- **Database doesn't exist**: Run the CREATE DATABASE command above

