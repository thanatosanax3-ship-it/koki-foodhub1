#!/usr/bin/env python
"""List all users in the system"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User

print("\n" + "="*60)
print("EXISTING USERS IN THE SYSTEM")
print("="*60 + "\n")

users = User.objects.all()

if not users:
    print("❌ No users found in the database.\n")
else:
    print(f"Total Users: {users.count()}\n")
    for u in users:
        print(f"Username: {u.username}")
        print(f"Email: {u.email}")
        print(f"Is Staff: {u.is_staff}")
        print(f"Is Superuser: {u.is_superuser}")
        print(f"Date Joined: {u.date_joined}")
        print("-" * 40)

print("\n⚠️  NOTE: Django hashes passwords for security.")
print("You cannot view plain text passwords.")
print("To reset a user's password, use:")
print("  python manage.py changepassword <username>\n")
