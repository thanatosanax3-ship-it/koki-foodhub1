import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','koki_foodhub.settings')
django.setup()
from django.test import Client
c = Client()
resp = c.get('/product-forecast/')
print('Status:', resp.status_code)
html = resp.content.decode()
print('Download-green button present:', 'download-green' in html)
print('Monthly active present:', '<button class="btn small range-btn active" data-range="30"' in html or 'Monthly' in html)
print('Hero best name present:', 'hero-best-name' in html)
print('\nSnippet:\n', html[:1000])
