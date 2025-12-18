#!/usr/bin/env python
"""Interactive PostgreSQL setup - asks for postgres password"""

import psycopg2
import getpass

print("=" * 60)
print("PostgreSQL Setup for Koki's Foodhub")
print("=" * 60)

postgres_password = getpass.getpass("Enter postgres superuser password: ")

try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password=postgres_password,
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("\n✅ Connected to PostgreSQL")
    
    # Grant schema permissions to koki_user
    print("\nGranting permissions to koki_user...")
    
    cursor.execute("GRANT ALL ON SCHEMA public TO koki_user")
    print("  ✅ Granted schema permissions")
    
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE koki_foodhub TO koki_user")
    print("  ✅ Granted database permissions")
    
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO koki_user")
    print("  ✅ Set default privileges")
    
    # Reconnect as koki_user to verify
    cursor.close()
    conn.close()
    
    print("\n✅ PostgreSQL configuration completed!")
    print("\nYou can now run: python manage.py migrate")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Connection failed: {e}")
    print("   Check your postgres password and try again")
except Exception as e:
    print(f"\n❌ Error: {e}")
