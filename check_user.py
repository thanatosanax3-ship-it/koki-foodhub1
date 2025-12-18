import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User

for user in User.objects.all():
    groups = list(user.groups.values_list('name', flat=True))
    print(f"{user.username:15} | groups: {str(groups):30} | is_staff: {user.is_staff} | is_superuser: {user.is_superuser}")
