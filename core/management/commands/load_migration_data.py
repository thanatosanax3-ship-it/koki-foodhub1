"""
Management command to load migration data
This runs after migrations to populate the database
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Load exported data from JSON files'

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        users_file = base_dir / 'users_export.json'
        products_file = base_dir / 'products_export.json'
        
        if users_file.exists():
            self.stdout.write(f"→ Loading users from {users_file.name}...")
            try:
                call_command('loaddata', str(users_file), verbosity=1)
                self.stdout.write(self.style.SUCCESS("✅ Users loaded"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Error loading users: {e}"))
        else:
            self.stdout.write(f"ℹ️ Users file not found: {users_file}")
        
        if products_file.exists():
            self.stdout.write(f"→ Loading products from {products_file.name}...")
            try:
                call_command('loaddata', str(products_file), verbosity=1)
                self.stdout.write(self.style.SUCCESS("✅ Products loaded"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Error loading products: {e}"))
        else:
            self.stdout.write(f"ℹ️ Products file not found: {products_file}")
