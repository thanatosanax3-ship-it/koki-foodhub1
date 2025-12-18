import psycopg2

conn = psycopg2.connect(
    dbname='koki_foodhub',
    user='koki_user',
    password='koki_secure_pass',
    host='localhost',
    port='5432'
)
conn.autocommit = True
cursor = conn.cursor()

try:
    # Check current user permissions
    cursor.execute("SELECT current_user")
    user = cursor.fetchone()[0]
    print(f'Connected as: {user}')
    
    # Check if we can create a test table
    cursor.execute("CREATE TABLE test_table (id SERIAL PRIMARY KEY)")
    print('✅ Can create tables')
    cursor.execute("DROP TABLE test_table")
    
except psycopg2.errors.InsufficientPrivilege as e:
    print(f'❌ Permission denied: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
finally:
    cursor.close()
    conn.close()
