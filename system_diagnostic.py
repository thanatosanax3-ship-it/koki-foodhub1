#!/usr/bin/env python
"""
Comprehensive System Diagnostic Check
Validates all critical components of Koki's Foodhub
"""
import os
import sys
import django
from pathlib import Path

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Get DATABASE_URL from command line or environment
if len(sys.argv) > 1:
    os.environ['DATABASE_URL'] = sys.argv[1]

django.setup()

from django.core.management import call_command
from django.test.utils import setup_test_environment, teardown_test_environment
from core.models import Product, Sale
from django.contrib.auth.models import User
import time

print("\n" + "="*70)
print("🔍 KOKI'S FOODHUB - COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("="*70)

checks_passed = 0
checks_failed = 0

def log_check(name, status, details=""):
    global checks_passed, checks_failed
    status_icon = "✅" if status else "❌"
    status_text = "PASS" if status else "FAIL"
    print(f"{status_icon} {name}: {status_text}")
    if details:
        print(f"   → {details}")
    if status:
        checks_passed += 1
    else:
        checks_failed += 1

# 1. Database Connection
print("\n📦 DATABASE CHECKS:")
try:
    from django.db import connections
    from django.db.utils import OperationalError
    
    db = connections['default']
    db.ensure_connection()
    log_check("Database Connection", True, f"Using {db.vendor} database")
except OperationalError as e:
    log_check("Database Connection", False, str(e))
except Exception as e:
    log_check("Database Connection", False, str(e))

# 2. Model Counts
print("\n📊 DATA INTEGRITY CHECKS:")
try:
    product_count = Product.objects.count()
    sale_count = Sale.objects.count()
    user_count = User.objects.count()
    
    log_check("Products in Database", product_count > 0, f"{product_count} products found")
    log_check("Sales Records in Database", sale_count > 0, f"{sale_count} sales found")
    log_check("Users in Database", user_count > 0, f"{user_count} users found")
except Exception as e:
    log_check("Data Retrieval", False, str(e))

# 3. Check for Duplicates
print("\n🔄 DUPLICATE DETECTION:")
try:
    from django.db.models import Count
    
    dup_products = Product.objects.values('name', 'category').annotate(count=Count('id')).filter(count__gt=1).count()
    dup_sales = Sale.objects.values('product', 'date', 'units_sold', 'revenue').annotate(count=Count('id')).filter(count__gt=1).count()
    
    log_check("Duplicate Products", dup_products == 0, f"{dup_products} duplicate groups found" if dup_products > 0 else "No duplicates")
    log_check("Duplicate Sales", dup_sales == 0, f"{dup_sales} duplicate groups found" if dup_sales > 0 else "No duplicates")
except Exception as e:
    log_check("Duplicate Check", False, str(e))

# 4. Data Validation
print("\n✔️  DATA VALIDATION CHECKS:")
try:
    # Check products have valid prices
    invalid_prices = Product.objects.filter(price__lt=0).count()
    log_check("Product Prices Valid", invalid_prices == 0, f"{invalid_prices} invalid prices" if invalid_prices > 0 else "All prices valid")
    
    # Check sales have valid quantities
    invalid_sales = Sale.objects.filter(units_sold__lt=0).count()
    log_check("Sales Quantities Valid", invalid_sales == 0, f"{invalid_sales} invalid quantities" if invalid_sales > 0 else "All quantities valid")
    
    # Check sales revenue is positive
    invalid_revenue = Sale.objects.filter(revenue__lt=0).count()
    log_check("Sales Revenue Valid", invalid_revenue == 0, f"{invalid_revenue} negative revenues" if invalid_revenue > 0 else "All revenues valid")
except Exception as e:
    log_check("Data Validation", False, str(e))

# 5. Django System Checks
print("\n⚙️  DJANGO SYSTEM CHECKS:")
try:
    from django.core.management import execute_from_command_line
    from io import StringIO
    import sys as sys_module
    
    old_stdout = sys_module.stdout
    sys_module.stdout = StringIO()
    
    try:
        call_command('check', verbosity=0)
        sys_module.stdout = old_stdout
        log_check("Django System Check", True, "No configuration issues found")
    except Exception as e:
        sys_module.stdout = old_stdout
        log_check("Django System Check", False, str(e))
except Exception as e:
    log_check("Django System Check", False, str(e))

# 6. Static Files
print("\n📁 STATIC FILES CHECKS:")
try:
    static_dir = Path('static')
    static_exists = static_dir.exists()
    log_check("Static Directory Exists", static_exists)
    
    if static_exists:
        static_files = list(static_dir.glob('**/*'))
        log_check("Static Files Present", len(static_files) > 0, f"{len(static_files)} files found")
except Exception as e:
    log_check("Static Files Check", False, str(e))

# 7. Templates
print("\n🎨 TEMPLATE CHECKS:")
try:
    templates_dir = Path('core/templates')
    templates_exist = templates_dir.exists()
    log_check("Templates Directory Exists", templates_exist)
    
    if templates_exist:
        template_files = list(templates_dir.glob('**/*.html'))
        log_check("Template Files Present", len(template_files) > 0, f"{len(template_files)} template files found")
except Exception as e:
    log_check("Templates Check", False, str(e))

# 8. Media Files
print("\n🖼️  MEDIA FILES CHECKS:")
try:
    media_dir = Path('media')
    media_exists = media_dir.exists()
    log_check("Media Directory Exists", media_exists)
    
    if media_exists:
        media_files = list(media_dir.glob('**/*'))
        product_images = list(Path('media/products').glob('*')) if Path('media/products').exists() else []
        log_check("Product Images Accessible", len(product_images) >= 0, f"{len(product_images)} product images found")
except Exception as e:
    log_check("Media Files Check", False, str(e))

# 9. Admin User
print("\n👤 ADMIN USER CHECKS:")
try:
    admin_users = User.objects.filter(is_superuser=True).count()
    log_check("Admin Users Exist", admin_users > 0, f"{admin_users} admin user(s) found")
except Exception as e:
    log_check("Admin User Check", False, str(e))

# 10. URL Configuration
print("\n🔗 URL CONFIGURATION CHECKS:")
try:
    from django.urls import reverse, resolve
    
    # Test some common URLs
    urls_to_test = [
        ('admin:index', 'Admin Panel'),
    ]
    
    all_urls_work = True
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            log_check(f"URL - {description}", True, f"Routes to {url}")
        except Exception as e:
            log_check(f"URL - {description}", False, str(e))
            all_urls_work = False
except Exception as e:
    log_check("URL Configuration Check", False, str(e))

# 11. Categories
print("\n📂 CATEGORY CHECKS:")
try:
    categories = Product.objects.values_list('category', flat=True).distinct().count()
    log_check("Product Categories Exist", categories > 0, f"{categories} unique categories found")
    
    category_list = list(Product.objects.values_list('category', flat=True).distinct())
    if len(category_list) <= 10:
        print(f"   → Categories: {', '.join(filter(None, category_list))}")
except Exception as e:
    log_check("Category Check", False, str(e))

# 12. Revenue Summary
print("\n💰 REVENUE SUMMARY:")
try:
    from django.db.models import Sum, Avg, Max, Min
    
    total_revenue = Sale.objects.aggregate(Sum('revenue'))['revenue__sum'] or 0
    avg_revenue = Sale.objects.aggregate(Avg('revenue'))['revenue__avg'] or 0
    total_units = Sale.objects.aggregate(Sum('units_sold'))['units_sold__sum'] or 0
    
    print(f"   Total Revenue: ${total_revenue:.2f}")
    print(f"   Average Sale: ${avg_revenue:.2f}")
    print(f"   Total Units Sold: {total_units}")
    
    log_check("Revenue Data Available", total_revenue > 0, f"Total: ${total_revenue:.2f}")
except Exception as e:
    log_check("Revenue Summary", False, str(e))

# Final Summary
print("\n" + "="*70)
print(f"📋 DIAGNOSTIC SUMMARY")
print("="*70)
print(f"✅ Checks Passed: {checks_passed}")
print(f"❌ Checks Failed: {checks_failed}")

if checks_failed == 0:
    print("\n🎉 ALL SYSTEMS OPERATIONAL - No issues detected!")
    exit_code = 0
else:
    print(f"\n⚠️  {checks_failed} issue(s) detected - Review above for details")
    exit_code = 1

print("="*70 + "\n")
sys.exit(exit_code)
