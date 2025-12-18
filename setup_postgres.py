#!/usr/bin/env python
"""Fix PostgreSQL permissions for koki_user"""

import psycopg2
import os
import sys

# Get postgres password from environment or ask user
postgres_password = os.getenv('POSTGRES_ROOT_PASSWORD', 'postgres')

try:
    # Connect as postgres superuser
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password=postgres_password,
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Connected to PostgreSQL as postgres...")
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'koki_foodhub'")
    if not cursor.fetchone():
        print("Creating database koki_foodhub...")
        cursor.execute("CREATE DATABASE koki_foodhub")
    else:
        print("Database koki_foodhub already exists")
    
    # Recreate user with proper permissions
    try:
        cursor.execute("DROP USER IF EXISTS koki_user")
        print("Dropped existing koki_user")
    except:
        pass
    
    # Create user with password
    cursor.execute("CREATE USER koki_user WITH PASSWORD 'koki_secure_pass'")
    print("Created koki_user")
    
    # Grant schema creation permission
    cursor.execute("GRANT ALL ON SCHEMA public TO koki_user")
    print("Granted schema permissions")
    
    # Grant database permissions
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE koki_foodhub TO koki_user")
    print("Granted database permissions")
    
    # Set default privileges
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO koki_user")
    print("Set default privileges")
    
    # Set role parameters
    cursor.execute("ALTER ROLE koki_user SET client_encoding TO 'utf8'")
    cursor.execute("ALTER ROLE koki_user SET default_transaction_isolation TO 'read committed'")
    cursor.execute("ALTER ROLE koki_user SET default_transaction_deferrable TO on")
    cursor.execute("ALTER ROLE koki_user SET timezone TO 'UTC'")
    print("Set role parameters")
    
    print("\n✅ PostgreSQL configuration completed successfully!")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check your postgres password")
    print("3. Run: python setup_postgres.py")
    print("\nOr set the password via environment:")
    print("  export POSTGRES_ROOT_PASSWORD=your_password")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
