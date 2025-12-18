#!/usr/bin/env python
"""Fix PostgreSQL schema permissions for koki_user"""

import psycopg2
import getpass

postgres_password = getpass.getpass("Enter postgres superuser password: ")

try:
    conn = psycopg2.connect(
        dbname='koki_foodhub',
        user='postgres',
        password=postgres_password,
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Setting comprehensive permissions...\n")
    
    # Grant schema permissions
    cursor.execute("GRANT ALL ON SCHEMA public TO koki_user")
    print("✅ Granted schema permissions to public")
    
    # Set ownership
    cursor.execute("ALTER SCHEMA public OWNER TO koki_user")
    print("✅ Set koki_user as schema owner")
    
    # Grant database permissions
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE koki_foodhub TO koki_user")
    print("✅ Granted database permissions")
    
    # Set default privileges for tables
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO koki_user")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO koki_user")
    print("✅ Set default privileges")
    
    cursor.close()
    conn.close()
    
    print("\n✅ All permissions set! Try migration now.")
    
except Exception as e:
    print(f"❌ Error: {e}")
