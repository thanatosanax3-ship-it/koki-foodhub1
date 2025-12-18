from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_product_price_large_product_price_medium_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
    ]
