import os
import sys
import django

# Ensure project root is on sys.path and settings module is set
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from core.views import sales_dashboard

User = get_user_model()
user = User.objects.filter(is_active=True).first()
if not user:
    print('no active user found')
    sys.exit(0)

rf = RequestFactory()
req = rf.get('/sales-dashboard/?debug_sales=1')
req.user = user
resp = sales_dashboard(req)
c = resp.content.decode('utf-8')
print('status', getattr(resp, 'status_code', None))
print('has today-orders-data', 'today-orders-data' in c)
start = c.find('id="today-orders-data"')
print('pos:', start)
if start != -1:
    print(c[start:start+800])
else:
    print('page snippet (first 1000 chars):')
    print(c[:1000])
