from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    now = timezone.now()
    Product.objects.filter(created_at__isnull=True).update(created_at=now)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_add_created_at_nullable'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
