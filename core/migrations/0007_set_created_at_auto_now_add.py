from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_backfill_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
