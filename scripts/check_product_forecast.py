import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','koki_foodhub.settings')
import django
django.setup()
from django.test import Client
c=Client()
# try to login using known admin username 'joanna' - default test password may not be set; we'll try without login
resp=c.get('/product-forecast/')
print('Status:', resp.status_code)
print('Len:', len(resp.content))
print(resp.content[:400].decode('utf-8','replace'))
