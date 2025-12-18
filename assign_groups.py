#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User, Group

# Get or create groups
admin_group, _ = Group.objects.get_or_create(name='Admin')
cashier_group, _ = Group.objects.get_or_create(name='Cashier')

# Get the first active user
user = User.objects.filter(is_active=True).first()

if user:
    user.groups.add(admin_group)
    print(f'✓ Added {user.username} to Admin group')
    print(f'✓ User groups: {list(user.groups.values_list("name", flat=True))}')
else:
    print('No active users found')
