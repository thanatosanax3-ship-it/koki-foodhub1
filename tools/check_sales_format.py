import os
import sys
import pathlib
import django

# Ensure project root is on sys.path so Django settings package can be imported
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Sale

qs = Sale.objects.order_by('-id')[:10]
print('Count:', qs.count())
formatted = []
for s in qs:
    print('id', s.id, 'date', getattr(s, 'date', None))
    if getattr(s, 'date', None):
        try:
            time_str = s.date.strftime('%I:%M:%S %p').lstrip('0')
        except Exception:
            time_str = s.date.isoformat()
    else:
        time_str = ''
    formatted.append(time_str)

print('formatted:', formatted)
