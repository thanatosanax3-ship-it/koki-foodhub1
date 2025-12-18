import os
import sys
# ensure project root on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','koki_foodhub.settings')
import django
django.setup()
from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from django.urls import resolve
from django.conf import settings
from django.test import Client

urls = ['/', '/login/', '/signup/', '/sales-dashboard/', '/products/', '/inventory/', '/sales/']

client = Client()
# try unauthenticated requests first
print('Unauthenticated checks:')
for u in urls:
    resp = client.get(u)
    print(u, resp.status_code, ('login page' if b'Login' in resp.content[:200] else 'ok'))

# find an active user
User = get_user_model()
user = User.objects.filter(is_active=True).first()
if not user:
    print('No active user to authenticate as; skipping auth checks')
    sys.exit(0)

# login via client
client.force_login(user)
print('\nAuthenticated checks as', user.username)
for u in urls:
    resp = client.get(u)
    print(u, resp.status_code)
    # print small snippet
    s = resp.content.decode('utf-8')
    print(' snippet:', s[:200].replace('\n',' '))
