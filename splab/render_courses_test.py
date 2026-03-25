import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splab.settings')
import django
django.setup()
from django.test import Client

c = Client()
resp = c.get('/courses/', HTTP_HOST='localhost')
print('STATUS:', resp.status_code)
content = resp.content.decode('utf-8', errors='replace')
print(content[:1200])
