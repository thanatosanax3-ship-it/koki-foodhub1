# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.db.models.functions import Lower
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import close_old_connections
from django.db import utils as db_utils
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import logging
import json
import traceback
import os
from django.http import JsonResponse, FileResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth import logout as auth_logout
import base64

from .models import Product, InventoryItem, Sale
from .forms import ProductForm, InventoryForm, SaleForm
from .auth import group_required  # new: role guard
from django.views.decorators.http import require_http_methods

def product_image(request, product_id):
    """Serve product image - handles missing files gracefully"""
    try:
        product = get_object_or_404(Product, pk=product_id)
        
        if not product.image:
            # Return a 404 so client can show placeholder
            return HttpResponse(status=404)
        
        # Try to read the image file
        try:
            with open(product.image.path, 'rb') as f:
                image_data = f.read()
            
            # Determine content type
            import mimetypes
            content_type = mimetypes.guess_type(product.image.name)[0] or 'image/jpeg'
            
            response = HttpResponse(image_data, content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'  # Cache for 1 day
            return response
        except FileNotFoundError:
            # Image record exists but file doesn't - return 404
            return HttpResponse(status=404)
    except Exception as e:
        logging.error(f'Error serving product image {product_id}: {str(e)}')
        return HttpResponse(status=500)

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'pages/signup.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'pages/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'pages/signup.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Assign selected role/group if provided. Allowed roles: Cashier and Owner.
        role = request.POST.get('role', '').strip()
        if role == 'Owner':
            grp, _ = Group.objects.get_or_create(name='Owner')
            user.groups.add(grp)
            user.save()
            # Owner accounts can login immediately
            try:
                auth_user = authenticate(request, username=username, password=password)
                if auth_user:
                    auth_login(request, auth_user)
                    messages.success(request, 'Owner account created and logged in successfully!')
                    return redirect('dashboard')
            except Exception:
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')

        elif role == 'Cashier':
            # Cashier registrations require Owner approval. Create user as inactive
            # and add to a 'PendingCashier' group so owners can review and approve.
            pending_grp, _ = Group.objects.get_or_create(name='PendingCashier')
            user.groups.add(pending_grp)
            user.is_active = False
            user.save()
            messages.success(request, 'Account created and is pending Owner approval. You will be notified when approved.')
            return redirect('login')

        else:
            # No role selected or unknown role — create account without group and allow login
            try:
                auth_user = authenticate(request, username=username, password=password)
                if auth_user:
                    auth_login(request, auth_user)
                    messages.success(request, 'Account created and logged in successfully!')
                    return redirect('dashboard')
            except Exception:
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
    
    return render(request, 'pages/signup.html')


def logout_view(request):
    """Log out the user on GET or POST and redirect to login."""
    try:
        auth_logout(request)
    except Exception:
        pass
    return redirect('login')

@login_required
def profile(request):
    return render(request, "pages/profile.html", {})

# Dashboard: any authenticated user
@login_required
def dashboard(request):
    top_products = Sale.objects.values("product__name").annotate(
        total_units=Sum("units_sold"), total_revenue=Sum("revenue")
    ).order_by("-total_units")[:5]

    low_stock = [i for i in InventoryItem.objects.select_related("product").all() if i.is_low_stock()]
    
    # Get all products with inventory info
    all_products = Product.objects.all().prefetch_related('inventory_items')
    products_data = []
    categories_set = set()
    
    for product in all_products:
        inv = product.inventory_items.first() if product.inventory_items.exists() else None
        # Normalize name display (replace underscores, title case) - WITHOUT the size suffix
        pretty_name = product.name.replace('_', ' ').title()
        
        # Build size-price mapping with automatic multipliers
        # Small: base - 5, Medium: Regular + 5, Large: base + 10
        base_price = float(product.price)
        size_prices = {}
        if product.size:
            size_prices = {
                'S': max(0, base_price - 5),        # Small: -5
                'M': base_price + 5,                 # Medium: Regular +5
                'L': base_price + 10,                # Large: +10
                'XL': base_price + 15,               # XL: +15 (bonus)
                'XXL': base_price + 20,              # XXL: +20 (bonus)
                'Regular': base_price,               # Regular: base
            }
        
        products_data.append({
            'id': product.id,
            'name': pretty_name,
            'price': base_price,
            'category': product.category,
            'size': product.size,
            'size_prices': size_prices,
            'quantity': inv.quantity if inv else 0,
            'is_low_stock': inv.is_low_stock() if inv else False,
            'image': product.image.url if product.image else None
        })
        categories_set.add(product.category)
    
    # Sort categories for consistent display
    categories = sorted([c for c in categories_set if c])
    
    context = {
        "top_products": top_products,
        "low_stock": low_stock,
        "all_products": products_data,
        "categories": categories
    }
    return render(request, "pages/dashboard.html", context)


def healthz(request):
    """Lightweight health endpoint used for quick production checks (no DB access)."""
    return HttpResponse("OK")

# Products: Admin only (read), Cashier can view
def product_list(request):
    # Inline, resilient permission checks instead of decorator to avoid
    # decorator-related failures on some deployments. This preserves the
    # original semantics: Owners bypass checks, and Admin/Cashier may view.
    logger = logging.getLogger(__name__)
    try:
        try:
            # If user is not authenticated, redirect to login (matches @login_required)
            if not request.user or not request.user.is_authenticated:
                return redirect('login')

            # Owner bypass
            if request.user.groups.filter(name='Owner').exists():
                allowed = True
            else:
                allowed = request.user.groups.filter(name__in=("Admin", "Cashier")).exists()

            if not allowed:
                return HttpResponseForbidden("You do not have permission to access this resource.")
        except Exception as perm_exc:
            # Be forgiving: log and continue — worst case the view will still try to render.
            logger.warning('Permission check failed (falling back to safe default): %s', str(perm_exc))

        sort = request.GET.get('sort', '')
        products = Product.objects.all()
        if sort == 'price-asc':
            products = products.order_by('price')
        elif sort == 'price-desc':
            products = products.order_by('-price')
        elif sort == 'name':
            # Case-insensitive alphabetical sort so lowercase names (e.g. "burger")
            # appear in the expected A → Z order.
            products = products.order_by(Lower('name'))
        elif sort == 'newest':
            # uses created_at for accurate ordering
            products = products.order_by('-created_at')

        return render(request, "pages/product_list.html", {"products": products, "sort": sort})
    except Exception as e:
        # Log traceback explicitly so hosting logs capture the error
        logger.exception('Unhandled exception in product_list: %s', str(e))
        return HttpResponse('Server Error (500) - An unexpected error occurred while listing products.', status=500)

@group_required("Admin", "Cashier")
def product_create(request):
    logger = logging.getLogger(__name__)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        try:
            # Ensure media directory exists before attempting to save image
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                os.makedirs(media_root, exist_ok=True)
                logger.info(f'Created media directory: {media_root}')
            
            # Also ensure products subdirectory exists
            products_dir = os.path.join(media_root, 'products')
            if not os.path.exists(products_dir):
                os.makedirs(products_dir, exist_ok=True)
                logger.info(f'Created products directory: {products_dir}')
            
            if form.is_valid():
                product = form.save(commit=False)
                # Ensure created_at is set
                if not product.created_at:
                    product.created_at = timezone.now()
                product.save()
                logger.info(f'Product created successfully: {product.name} (ID: {product.id})')
                messages.success(request, "Product created successfully.")
                return redirect("product_list")
            else:
                # Form invalid - render with errors
                logger.warning(f'Form validation failed: {form.errors}')
                messages.error(request, "Please correct the errors below.")
        except Exception as e:
            # Log full traceback and show friendly message instead of 500
            logger.error('Error in product_create: %s', str(e))
            logger.error('Traceback:\n%s', traceback.format_exc())
            messages.error(request, f"Error creating product: {str(e)[:100]}")
    else:
        form = ProductForm()
    return render(request, "pages/product_form.html", {"form": form, "title": "Create Product"})

@group_required("Admin", "Cashier")
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "pages/product_form.html", {"form": form, "title": "Edit Product"})

@group_required("Admin", "Cashier")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "pages/product_form.html", {"form": None, "title": "Delete Product", "confirm": True})

# Inventory: Admin only
@group_required("Admin")
def inventory_list(request):
    items = InventoryItem.objects.select_related("product").all()
    return render(request, "pages/inventory_list.html", {"items": items})

@group_required("Admin")
def inventory_create(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item created.")
            return redirect("inventory_list")
    else:
        form = InventoryForm()
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Create Inventory Item"})

@group_required("Admin")
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item updated.")
            return redirect("inventory_list")
    else:
        form = InventoryForm(instance=item)
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Edit Inventory Item"})

@group_required("Admin")
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Inventory item deleted.")
        return redirect("inventory_list")
    return render(request, "pages/inventory_form.html", {"form": None, "title": "Delete Inventory Item", "confirm": True})

# Sales: Admin only (Cashier should not access sales list page)
@group_required("Admin")
def sale_list(request):
    sales = Sale.objects.select_related("product").all()
    return render(request, "pages/sale_list.html", {"sales": sales})

@group_required("Admin")
@group_required("Admin", "Cashier")
def sale_create(request):
    # Redirect to the sales period form for automatic reporting
    return redirect('record_sales_period')

@group_required("Admin")
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Sale updated.")
            return redirect("sale_list")
    else:
        form = SaleForm(instance=sale)
    return render(request, "pages/sale_form.html", {"form": form, "title": "Edit Sale"})

@group_required("Admin")
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted.")
        return redirect("sale_list")
    return render(request, "pages/sale_form.html", {"form": None, "title": "Delete Sale", "confirm": True})

# Sales Dashboard: any authenticated user
@login_required
def sales_dashboard(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    # Total sales and orders
    total_sales = Sale.objects.aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0
    total_orders = Sale.objects.count()
    avg_order = (total_sales / total_orders) if total_orders else 0

    # Top selling items (by units)
    top_items_qs = (
        Sale.objects.values('product__name')
        .annotate(units_sold=Sum('units_sold'), revenue=Sum('revenue'))
        .order_by('-units_sold')[:5]
    )
    top_items = [{'product': t['product__name'], 'units': t['units_sold'], 'revenue': float(t['revenue'])} for t in top_items_qs]

    # Recent sales history (last 20 sale records)
    recent_qs = Sale.objects.select_related('product').order_by('-id')[:20]
    recent_sales = []
    for s in recent_qs:
        # Format time in a portable way: avoid platform-specific flags like '%-I'
        time_str = ''
        if getattr(s, 'date', None):
            try:
                # Use %I for hour (12-hour clock) and strip any leading zero for prettier display
                time_str = s.date.strftime('%I:%M:%S %p').lstrip('0')
            except Exception:
                # Fallback to ISO format if strftime fails for any reason
                time_str = getattr(s, 'date').isoformat()

        recent_sales.append({
            'item': s.product.name,
            'qty': s.units_sold,
            'price': float(s.revenue) / s.units_sold if s.units_sold else 0,
            'total': float(s.revenue),
            'time': time_str
        })

    # Sales by category (sum units and revenue)
    cat_qs = (
        Sale.objects.select_related('product')
        .values('product__category')
        .annotate(units=Sum('units_sold'), revenue=Sum('revenue'))
    )
    category_sales = []
    for c in cat_qs:
        category_sales.append({'category': c['product__category'] or 'Uncategorized', 'quantity': int(c['units'] or 0), 'revenue': float(c['revenue'] or 0)})

    # Daily totals (last 7 days)
    # Use server local date to match how dates are stored/displayed
    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()
    start_date = today - timedelta(days=6)
    try:
        # Avoid DB-specific TruncDate by aggregating in Python which is portable across backends
        sales_for_days = Sale.objects.filter(date__gte=start_date).values('date', 'revenue')
        day_map = {}
        for rec in sales_for_days:
            d = rec.get('date')
            if d is None:
                continue
            # ensure d is a date
            if hasattr(d, 'date'):
                d = d.date()
            entry = day_map.setdefault(d, {'revenue': 0.0, 'orders': 0})
            entry['revenue'] += float(rec.get('revenue') or 0)
            entry['orders'] += 1

        daily_sales = [
            {'day': day, 'revenue': data['revenue'], 'orders': data['orders']}
            for day, data in sorted(day_map.items())
        ]
    except Exception as e:
        logging.getLogger(__name__).exception('Failed to compute daily_sales: %s', e)
        daily_sales = []

    # Weekly totals (last 4 weeks) - compute in Python to avoid DB-specific TruncWeek issues
    start_week = today - timedelta(weeks=3)
    weekly_sales = []
    try:
        weekly_map = {}
        sales_for_weeks = Sale.objects.filter(date__gte=start_week).values('date', 'revenue')
        for rec in sales_for_weeks:
            d = rec.get('date')
            if d is None:
                continue
            # Normalize to date if datetime
            if hasattr(d, 'date'):
                d = d.date()
            # Compute week start (Monday)
            week_start = d - timedelta(days=d.weekday())
            entry = weekly_map.setdefault(week_start, {'revenue': 0.0, 'orders': 0})
            entry['revenue'] += float(rec.get('revenue') or 0)
            entry['orders'] += 1

        weekly_sales = [
            {'week_start': wk, 'revenue': data['revenue'], 'orders': data['orders']}
            for wk, data in sorted(weekly_map.items())
        ]
    except Exception as e:
        logging.getLogger(__name__).exception('Failed to compute weekly_sales: %s', e)
        weekly_sales = []

    # Prepare context
    # Compute explicit today totals so client can rely on server-defined "today".
    # Use a direct DB aggregate to avoid DB-function issues (e.g. TruncDate failing on SQLite).
    try:
        today_agg = Sale.objects.filter(date=today).aggregate(today_revenue=Sum('revenue'), today_orders=Count('id'))
        today_orders = int(today_agg.get('today_orders') or 0)
        today_revenue = float(today_agg.get('today_revenue') or 0.0)
    except Exception:
        # Fallback to daily_sales if the aggregate fails
        today_entry = next((d for d in daily_sales if d.get('day') == today), None) if daily_sales else None
        today_orders = int(today_entry['orders']) if today_entry else 0
        today_revenue = float(today_entry['revenue']) if today_entry else 0.0
    today_label = str(today)
    # Provide a server-side ISO timestamp so the client can use the server's notion of "now"
    server_today_iso = timezone.localtime().isoformat()
    context = {
        'total_sales': float(total_sales),
        'total_orders': int(total_orders),
        'avg_order': float(avg_order),
        'top_items': top_items,
        'recent_sales': recent_sales,
        'category_sales': category_sales,
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'today_label': today_label,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'server_today_iso': server_today_iso,
    }
    return render(request, "pages/sales_dashboard.html", context)


@login_required
def sales_today_api(request):
    """Return JSON with today's sales totals (orders, revenue) and server timestamp."""
    from django.utils import timezone
    from django.db.models import Sum, Count

    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()

    try:
        agg = Sale.objects.filter(date=today).aggregate(today_revenue=Sum('revenue'), today_orders=Count('id'))
        orders = int(agg.get('today_orders') or 0)
        revenue = float(agg.get('today_revenue') or 0.0)
    except Exception:
        orders = 0
        revenue = 0.0

    server_today_iso = timezone.localtime().isoformat()
    return JsonResponse({'orders': orders, 'revenue': revenue, 'server_today_iso': server_today_iso})

# Forecast: any authenticated user
@login_required
def forecast_view(request):
    # Allow any authenticated user to view the forecast page. If you'd like
    # to restrict to Admins again, re-add `@group_required("Admin")` above.
    import json
    logger = logging.getLogger(__name__)

    # Ensure any stale DB connections are closed before we start heavy DB work
    # to avoid intermittent "connection already closed" errors seen in prod.
    try:
        close_old_connections()
    except Exception:
        # Ignore errors closing old connections; proceed and rely on Django to manage
        pass

    # We will rely only on DB historical sales (Sale objects) for forecasting.
    # No CSV-based forecasts will be used to avoid stale example data influencing predictions.
    import_error = None
    try:
        from .services.forecasting import aggregate_sales, forecast_time_series, moving_average_forecast
        import_error = None
    except Exception as exc:
        # Log the import error but continue with safe stubs so page renders
        logger.exception('Forecasting import failed: %s', str(exc))
        import_error = exc
        def moving_average_forecast(window=3):
            return {'db_forecasts': {}}
        def forecast_time_series(series, horizon=7, method='linear', window=3):
            vals = [v for _, v in (series or [])]
            if not vals:
                return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0, 'accuracy': 'Low'}
            recent = vals[-window:] if window and len(vals) >= 1 else vals
            avg = sum(recent) / len(recent)
            slope = 0.0
            if len(recent) >= 2:
                slope = (recent[-1] - recent[0]) / float(len(recent) - 1)
            preds = [max(0, int(round(avg + slope * (i + 1)))) for i in range(horizon)]
            mean = avg
            var = sum((x - mean) ** 2 for x in recent) / len(recent) if len(recent) else 0.0
            std = var ** 0.5
            upper = [int(round(p + 1.5 * std)) for p in preds]
            lower = [max(0, int(round(p - 1.5 * std))) for p in preds]
            confidence = 0.0 if mean <= 0 else max(0.0, min(100.0, (1.0 - (std / (mean + 1e-9))) * 100.0))
            accuracy = 'High' if confidence >= 70 else 'Medium' if confidence >= 40 else 'Low'
            return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': confidence, 'accuracy': accuracy}


    # Build per-product forecasts using DB historical sales only
    data = []
    try:
        db_results = moving_average_forecast(window=3)
        db_forecasts = db_results.get('db_forecasts', {})
        for pid, r in db_forecasts.items():
            try:
                product = Product.objects.get(pk=pid)
                confidence = r.get('confidence', 0)
                # normalise to percentage if method returned 0-1
                if confidence and confidence <= 1.0:
                    confidence = confidence * 100

                hist = r.get('history', []) or []
                last_7 = sum([u for _, u in hist[-7:]]) if hist else 0

                data.append({
                    "product": product.name,
                    "forecast": int(r.get('forecast', 0)),
                    "avg": float(r.get('avg', 0)),
                    "trend": r.get('trend', 'unknown'),
                    "confidence": int(confidence or 0),
                    "history": hist,
                    "last_7_days": int(last_7),
                    "source": "Database",
                    "is_csv": False
                })
            except Product.DoesNotExist:
                continue
    except Exception as e:
        logger.exception('Error generating per-product DB forecasts: %s', str(e))

    # Always use DB aggregate series for charts and forecasting
    try:
        db_daily = aggregate_sales('daily', lookback=60)
        db_weekly = aggregate_sales('weekly', lookback=12)
        db_monthly = aggregate_sales('monthly', lookback=12)

        daily_series = db_daily
        weekly_series = db_weekly
        monthly_series = db_monthly

        forecast_daily_base = db_daily
        forecast_weekly_base = db_weekly
        forecast_monthly_base = db_monthly

        daily_fore = forecast_time_series(forecast_daily_base, horizon=30)
        weekly_fore = forecast_time_series(forecast_weekly_base, horizon=12)
        monthly_fore = forecast_time_series(forecast_monthly_base, horizon=6)

        series_error = None
    except Exception as series_exc:
        logger.exception('Error generating time series or forecasts: %s', str(series_exc))
        daily_series, weekly_series, monthly_series = [], [], []
        daily_fore = {'forecast': [], 'upper': [], 'lower': [], 'confidence': 0}
        weekly_fore = {'forecast': [], 'upper': [], 'lower': [], 'confidence': 0}
        monthly_fore = {'forecast': [], 'upper': [], 'lower': [], 'confidence': 0}
        series_error = str(series_exc)

    # Simple analytics
    total_forecasted_units = sum(item['forecast'] for item in data)
    avg_confidence = sum(item['confidence'] for item in data) / len(data) if data else 0
    next_week_forecast = total_forecasted_units * 7
    peak_day = "Saturday"
    peak_orders = int(total_forecasted_units * 1.2)
    last_week_total = sum(item['last_7_days'] for item in data)
    growth_percentage = ((next_week_forecast - last_week_total) / last_week_total * 100) if last_week_total > 0 else 0

    # Compute period summaries (use DB actuals shown on charts)
    # Import helpers with defensive fallback so a missing dependency in production
    # doesn't cause the whole view to 500. If the import fails, we log and
    # provide simple stub implementations that return safe defaults.
    try:
        from .services.forecasting import compute_period_overview, generate_insight
    except Exception as e:
        logger.exception('Error importing period overview helpers: %s', str(e))

        def compute_period_overview(series):
            if not series:
                return {'total': 0, 'previous': 0, 'pct_change': 0.0, 'arrow': 'same'}
            cur_label, cur_val = series[-1]
            prev_val = series[-2][1] if len(series) >= 2 else 0
            total = int(cur_val)
            previous = int(prev_val)
            if previous == 0:
                pct = 100.0 if total > 0 else 0.0
            else:
                pct = round(((total - previous) / float(previous)) * 100.0, 2)
            if pct > 0:
                arrow = 'up'
            elif pct < 0:
                arrow = 'down'
            else:
                arrow = 'same'
            return {'total': total, 'previous': previous, 'pct_change': pct, 'arrow': arrow}

        def generate_insight(period_name, series, forecast_payload):
            return ''
    # Compute period summaries
    daily_summary = compute_period_overview(daily_series)
    weekly_summary = compute_period_overview(weekly_series)
    monthly_summary = compute_period_overview(monthly_series)

    # Compute currency-based sales totals (revenue) for the hero tiles so values
    # displayed with the currency symbol reflect actual revenue (not unit counts).
    from django.utils import timezone
    from django.db.models import Sum
    from datetime import timedelta

    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()

    try:
        today_revenue = float(Sale.objects.filter(date=today).aggregate(total=Sum('revenue')).get('total') or 0.0)
        week_start = today - timedelta(days=today.weekday())
        this_week_revenue = float(Sale.objects.filter(date__gte=week_start, date__lte=today).aggregate(total=Sum('revenue')).get('total') or 0.0)
        month_start = today.replace(day=1)
        this_month_revenue = float(Sale.objects.filter(date__gte=month_start, date__lte=today).aggregate(total=Sum('revenue')).get('total') or 0.0)
        # Also compute unit counts (units sold) for the same periods so we can
        # show "X units / PHPY" in the hero tiles for clarity.
        today_units = int(Sale.objects.filter(date=today).aggregate(total=Sum('units_sold')).get('total') or 0)
        this_week_units = int(Sale.objects.filter(date__gte=week_start, date__lte=today).aggregate(total=Sum('units_sold')).get('total') or 0)
        this_month_units = int(Sale.objects.filter(date__gte=month_start, date__lte=today).aggregate(total=Sum('units_sold')).get('total') or 0)
    except Exception:
        # Fallback to the previously-computed unit-based summaries if revenue aggregation fails
        today_revenue = float(daily_summary.get('total', 0))
        this_week_revenue = float(weekly_summary.get('total', 0))
        this_month_revenue = float(monthly_summary.get('total', 0))
        # daily_summary still contains unit counts — use them as fallbacks for units
        today_units = int(daily_summary.get('total', 0))
        this_week_units = int(weekly_summary.get('total', 0))
        this_month_units = int(monthly_summary.get('total', 0))

    # Forecast preview values (next period forecast) from forecast payloads
    today_forecast = (daily_fore.get('forecast') or [0])[0] if daily_fore.get('forecast') else 0
    week_forecast = (weekly_fore.get('forecast') or [0])[0] if weekly_fore.get('forecast') else 0
    month_forecast = (monthly_fore.get('forecast') or [0])[0] if monthly_fore.get('forecast') else 0

    # Data source: we use database historical sales only for forecasting
    data_source = 'db'

    # counts and date range
    def first_last(series):
        if not series:
            return (None, None)
        first = series[0][0]
        last = series[-1][0]
        return (first, last)

    d_first, d_last = first_last(daily_series)
    w_first, w_last = first_last(weekly_series)
    m_first, m_last = first_last(monthly_series)

    context = {
        "data": data,
        "total_forecast": next_week_forecast,
        "avg_confidence": avg_confidence,
        "peak_day": peak_day,
        "peak_orders": peak_orders,
        "growth_percentage": growth_percentage,
        # Use revenue (currency) values for the hero tiles so they're consistent
        # with other parts of the app that display monetary totals.
        # Use revenue (currency) values for the hero tiles so they're consistent
        # with other parts of the app that display monetary totals.
        "today_sales": today_revenue,
        "this_week_sales": this_week_revenue,
        "this_month_sales": this_month_revenue,
        # Unit counts to be shown alongside revenue in the hero tiles
        "today_units": today_units,
        "this_week_units": this_week_units,
        "this_month_units": this_month_units,
        "today_forecast_preview": today_forecast,
        "week_forecast_preview": week_forecast,
        "month_forecast_preview": month_forecast,
        "currency": "PHP",
        # Period summaries for server-side fallbacks in template
        "daily_summary": daily_summary,
        "weekly_summary": weekly_summary,
        "monthly_summary": monthly_summary,
        # Forecast confidences for server-side display
        "daily_confidence": daily_fore.get('confidence', 0),
        "weekly_confidence": weekly_fore.get('confidence', 0),
        "monthly_confidence": monthly_fore.get('confidence', 0),
        # JSON for charts
        "daily_json": json.dumps({
            'labels': [d for d, _ in daily_series],
            'actual': [v for _, v in daily_series],
            'forecast': daily_fore['forecast'],
            'upper': daily_fore['upper'],
            'lower': daily_fore['lower'],
            'confidence': daily_fore['confidence']
        }),
        "weekly_json": json.dumps({
            'labels': [d for d, _ in weekly_series],
            'actual': [v for _, v in weekly_series],
            'forecast': weekly_fore['forecast'],
            'upper': weekly_fore['upper'],
            'lower': weekly_fore['lower'],
            'confidence': weekly_fore['confidence']
        }),
        "monthly_json": json.dumps({
            'labels': [d for d, _ in monthly_series],
            'actual': [v for _, v in monthly_series],
            'forecast': monthly_fore['forecast'],
            'upper': monthly_fore['upper'],
            'lower': monthly_fore['lower'],
            'confidence': monthly_fore['confidence']
        })
    }

    # Allow enabling a server-side debug dump via ?debug=1 on the view (temporary troubleshooting)
    try:
        context['debug_mode'] = bool(request.GET.get('debug'))
    except Exception:
        context['debug_mode'] = False

    # include diagnostics
    context.update({
        'data_source': data_source,
        'daily_count': len(daily_series),
        'weekly_count': len(weekly_series),
        'monthly_count': len(monthly_series),
        'daily_first': d_first,
        'daily_last': d_last,
        'weekly_first': w_first,
        'weekly_last': w_last,
        'monthly_first': m_first,
        'monthly_last': m_last,
    })

    # If import or series generation failed, pass an error message to template so it can show a friendly alert
    if import_error:
        context['error_message'] = 'Forecasting functionality is currently unavailable on this instance. Check logs for details.'
    elif series_error:
        context['error_message'] = 'Forecast computation failed. Displaying limited results.'
    else:
        # If no DB series were produced, show friendly message
        if (not daily_series) and (not weekly_series) and (not monthly_series):
            context['error_message'] = 'No historical sales data available to generate forecasts.'

    try:
        # Render and set no-cache headers so browsers always fetch fresh computed values
        response = render(request, "pages/forecast.html", context)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response
    except db_utils.InterfaceError as ie:
        # Transient DB connection closed errors can occur on some deployments
        # (e.g. during a worker restart); attempt to close stale connections
        # and retry the render once before returning a 500.
        logger = logging.getLogger(__name__)
        logger.warning('InterfaceError during render; retrying after close_old_connections: %s', str(ie))
        try:
            close_old_connections()
            response = render(request, "pages/forecast.html", context)
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            return response
        except Exception as render_exc:
            # fall through to the common error handler below
            pass
    except Exception as render_exc:
        import traceback, uuid
        tb = traceback.format_exc()
        error_id = uuid.uuid4().hex[:8]
        logger = logging.getLogger(__name__)
        # Log the full traceback with an identifier so we can correlate production logs
        logger.exception('Error rendering forecast template (id=%s): %s\n%s', error_id, str(render_exc), tb)
        # If an admin requests with ?debug=1, return the full stack trace (temporary safe debugging aid)
        try:
            is_admin = hasattr(request, 'user') and getattr(request.user, 'is_superuser', False)
            if request.GET.get('debug') and is_admin:
                return HttpResponse('<pre style="white-space:pre-wrap;">Server Error (500) (id=' + error_id + ')\n\n' + tb + '</pre>', status=500)
        except Exception:
            # ignore and fall back to friendly message
            pass
        # Show a friendly error page with an error id so admins can look up logs
        return HttpResponse(f'Server Error (500) - Forecasts temporarily unavailable. Error ID: {error_id}', status=500)


from django.contrib.auth.decorators import login_required

@login_required
def forecast_data_api(request):
    """Return JSON with aggregated series and forecasts for daily/weekly/monthly and per-product summaries."""
    logger = logging.getLogger(__name__)
    try:
        user_info = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated'):
            try:
                groups = list(request.user.groups.values_list('name', flat=True))
            except Exception:
                groups = []
            user_info = {
                'username': getattr(request.user, 'username', None),
                'authenticated': bool(request.user.is_authenticated),
                'groups': groups
            }
        logger.info('forecast_data_api called; path=%s user=%s remote=%s x-requested-with=%s', request.path, user_info, request.META.get('REMOTE_ADDR'), request.META.get('HTTP_X_REQUESTED_WITH'))
    except Exception:
        logger.exception('Error logging forecast_data_api request info')
    # Wrap main API logic so unexpected exceptions return a controlled JSON error
    try:
        try:
            from .services.forecasting import aggregate_sales, forecast_time_series, moving_average_forecast
        except Exception as e:
            logger.exception('Forecast API import failed: %s', str(e))
            return JsonResponse({'error': 'Forecasting libraries unavailable', 'details': str(e)}, status=500)

        import json

        # Build per-product forecasts from DB historical sales only
        products = []
        try:
            db_results = moving_average_forecast(window=3)
            db_forecasts = db_results.get('db_forecasts', {})
            for pid, r in db_forecasts.items():
                try:
                    product_obj = Product.objects.get(pk=pid)
                except Product.DoesNotExist:
                    continue
                conf = r.get('confidence', 0)
                if conf and conf <= 1.0:
                    conf = conf * 100
                accuracy = r.get('accuracy') or ('High' if conf >= 70 else 'Medium' if conf >= 40 else 'Low')
                history = r.get('history', []) or []
                products.append({
                    'product': product_obj.name,
                    'product_id': pid,
                    'forecast': int(r.get('forecast', 0)),
                    'avg': float(r.get('avg', 0)),
                    'trend': r.get('trend', 'unknown'),
                    'confidence': int(conf or 0),
                    'accuracy': accuracy,
                    'last_7_days': int(sum([u for _, u in history[-7:]]))
                })
        except Exception as e:
            logger.exception('Error building DB product forecasts: %s', str(e))
            products = []
    except Exception as e:
        # Catch-all: return JSON error; include traceback when admin requests debug=1
        import traceback, uuid
        tb = traceback.format_exc()
        error_id = uuid.uuid4().hex[:8]
        logger.exception('Unexpected error in forecast_data_api (id=%s): %s\n%s', error_id, str(e), tb)
        try:
            is_admin = hasattr(request, 'user') and getattr(request.user, 'is_superuser', False)
            if request.GET.get('debug') and is_admin:
                return JsonResponse({'error': 'Internal Server Error', 'trace': tb, 'id': error_id}, status=500)
        except Exception:
            pass
        return JsonResponse({'error': 'Internal Server Error', 'id': error_id}, status=500)

    # Use DB aggregates for series (daily/weekly/monthly) — CSV is not used for forecasts
    daily_series = aggregate_sales('daily', lookback=60)
    weekly_series = aggregate_sales('weekly', lookback=12)
    monthly_series = aggregate_sales('monthly', lookback=12)

    # Optional filters from query params: start (YYYY-MM-DD), end (YYYY-MM-DD), product
    start = request.GET.get('start')
    end = request.GET.get('end')
    product_filter = request.GET.get('product')

    def filter_series_by_range(series, granularity):
        if not series or not (start or end):
            return series
        out = []
        for label, val in series:
            try:
                if granularity == 'monthly':
                    # label like 'YYYY-MM'
                    lab_key = label
                    if start:
                        if lab_key < start[:7]:
                            continue
                    if end:
                        if lab_key > end[:7]:
                            continue
                else:
                    # daily/weekly ISO date
                    lab_date = label
                    if start and lab_date < start:
                        continue
                    if end and lab_date > end:
                        continue
                out.append((label, val))
            except Exception:
                continue
        return out

    daily_series = filter_series_by_range(daily_series, 'daily')
    weekly_series = filter_series_by_range(weekly_series, 'weekly')
    monthly_series = filter_series_by_range(monthly_series, 'monthly')

    if product_filter:
        products = [p for p in products if p.get('product') == product_filter]

    try:
        daily_fore = forecast_time_series(daily_series, horizon=30)
        weekly_fore = forecast_time_series(weekly_series, horizon=12)
        monthly_fore = forecast_time_series(monthly_series, horizon=6)
    except Exception as e:
        import traceback, uuid
        tb = traceback.format_exc()
        error_id = uuid.uuid4().hex[:8]
        logger.exception('Error running forecast_time_series (id=%s): %s\n%s', error_id, str(e), tb)
        try:
            is_admin = hasattr(request, 'user') and getattr(request.user, 'is_superuser', False)
            if request.GET.get('debug') and is_admin:
                return JsonResponse({'error': 'Internal Server Error', 'trace': tb, 'id': error_id}, status=500)
        except Exception:
            pass
        return JsonResponse({'error': 'Internal Server Error', 'id': error_id}, status=500)

    try:
        from .services.forecasting import compute_period_overview, generate_insight

        # Build summary for overview cards and AI insights
        daily_summary = compute_period_overview(daily_series)
        weekly_summary = compute_period_overview(weekly_series)
        monthly_summary = compute_period_overview(monthly_series)

        daily_insight = generate_insight('daily', daily_series, daily_fore)
        weekly_insight = generate_insight('weekly', weekly_series, weekly_fore)
        monthly_insight = generate_insight('monthly', monthly_series, monthly_fore)

        payload = {
            'products': products,
            'data_source': 'db',
            'summary': {
                'daily': daily_summary,
                'weekly': weekly_summary,
                'monthly': monthly_summary
            },
            'ai_insights': [ins for ins in (daily_insight, weekly_insight, monthly_insight) if ins],
            'daily': {
                'labels': [d for d, _ in daily_series],
                'actual': [v for _, v in daily_series],
                'forecast': daily_fore['forecast'],
                'upper': daily_fore['upper'],
                'lower': daily_fore['lower'],
                'confidence': daily_fore['confidence'],
                'accuracy': daily_fore.get('accuracy', '')
            },
            'weekly': {
                'labels': [d for d, _ in weekly_series],
                'actual': [v for _, v in weekly_series],
                'forecast': weekly_fore['forecast'],
                'upper': weekly_fore['upper'],
                'lower': weekly_fore['lower'],
                'confidence': weekly_fore['confidence'],
                'accuracy': weekly_fore.get('accuracy', '')
            },
            'monthly': {
                'labels': [d for d, _ in monthly_series],
                'actual': [v for _, v in monthly_series],
                'forecast': monthly_fore['forecast'],
                'upper': monthly_fore['upper'],
                'lower': monthly_fore['lower'],
                'confidence': monthly_fore['confidence'],
                'accuracy': monthly_fore.get('accuracy', '')
            }
        }
        return JsonResponse(payload)
    except Exception as out_exc:
        logger.exception('Error building forecast API response: %s', str(out_exc))
        return JsonResponse({'error': 'Failed to build forecast response', 'details': str(out_exc)}, status=500)


@login_required
def product_forecast(request):
    """Render the product-level forecast page which fetches data from `product_forecast_api` via JS."""
    # Minimal server-side context; most data is fetched client-side for interactivity
    context = {
        'api_url': '/product-forecast/api/',
        'title': 'Product Forecast'
    }

    # Provide known product categories to the template for filter controls
    try:
        categories_qs = Product.objects.order_by('category').values_list('category', flat=True).distinct()
        categories = [c for c in categories_qs if c]
        context['categories'] = categories
    except Exception:
        context['categories'] = []
    logger = logging.getLogger(__name__)
    # Close any stale DB connections before rendering to avoid psycopg2.InterfaceError
    try:
        close_old_connections()
    except Exception:
        pass

    try:
        response = render(request, 'pages/product_forecast.html', context)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    except db_utils.InterfaceError as ie:
        # transient DB connection issue: try to close old connections and retry once
        logger.warning('InterfaceError when rendering product_forecast; retrying after close_old_connections: %s', str(ie))
        try:
            close_old_connections()
            response = render(request, 'pages/product_forecast.html', context)
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response
        except Exception:
            logger.exception('Retry render failed for product_forecast')
    except Exception as e:
        # Log full traceback for post-mortem on deployed systems
        import traceback, sys
        tb = traceback.format_exc()
        logger.exception('Error rendering product_forecast: %s\n%s', str(e), tb)
        # Try to render a minimal static fallback page so the endpoint remains functional
        # Render a minimal inline fallback without using templates to avoid any further DB queries
        simple_html = """
          <!doctype html>
          <html>
            <head><meta charset='utf-8'><title>Product Forecast (offline)</title></head>
            <body style="font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:24px;">
              <h1>Product Forecast (offline)</h1>
              <p>The interactive dashboard is temporarily unavailable. You can still access raw data at <a href="/product-forecast/api/">/product-forecast/api/</a></p>
            </body>
          </html>
        """
        resp = HttpResponse(simple_html, content_type='text/html')
        resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp

    # Last resort: return a simple textual error for monitoring
    return HttpResponse('Server Error (500) - unable to render product forecast', status=500)


@login_required
def product_forecast_api(request):
    """Return JSON payload with per-product multi-horizon forecasts and top-ranked lists.
    Optional query params:
      - horizon: one of '1','7','30' to select ranking horizon (default 7)
      - top: integer number of top products to return (default 10)
      - product_id: if provided, include a detailed series and forecast for this product
    """
    logger = logging.getLogger(__name__)
    try:
        from .services.forecasting import product_forecast_summary
    except Exception as exc:
        logger.exception('Forecast helpers unavailable: %s', str(exc))
        return JsonResponse({'error': 'Forecasting helpers unavailable', 'details': str(exc)}, status=500)

    horizon = int(request.GET.get('horizon', '7'))
    try:
        top_n = int(request.GET.get('top', '10'))
    except Exception:
        top_n = 10

    product_id = request.GET.get('product_id')
    category = request.GET.get('category')
    search = request.GET.get('search', '').strip()
    # New filters: active/in-stock and price range
    active_only = request.GET.get('active')
    in_stock_only = request.GET.get('in_stock')
    try:
        min_price = float(request.GET.get('min_price')) if request.GET.get('min_price') not in (None, '') else None
    except Exception:
        min_price = None
    try:
        max_price = float(request.GET.get('max_price')) if request.GET.get('max_price') not in (None, '') else None
    except Exception:
        max_price = None

    products_payload = []
    try:
        # Build base queryset with optional filters
        qs = Product.objects.all().order_by('name')
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(name__icontains=search)
        # Apply active filter
        if active_only in ('1', 'true', 'True'):
            qs = qs.filter(is_active=True)
        # Apply price filters
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        # If in_stock filter requested, narrow queryset to products with inventory quantity > 0
        if in_stock_only in ('1', 'true', 'True'):
            qs = qs.filter(inventory_items__quantity__gt=0).distinct()

        # Compute per-product summaries
        for p in qs:
            try:
                summ = product_forecast_summary(p.id, horizons=(1, 7, 30), lookback_days=180)
                # pick forecast for requested horizon
                h_key = f'h_{horizon}'
                hinfo = summ['horizons'].get(h_key, {'forecast': 0, 'confidence': 0})
                forecast_h = int(hinfo.get('forecast', 0))
                last_7 = int(summ.get('last_7_days', 0))
                # past 30 days
                vals = [v for _, v in summ.get('series', [])]
                past_30 = int(sum(vals[-30:])) if vals else 0
                # growth: compare forecast for horizon to last_7 (if horizon==7) or past_30 if horizon==30
                if horizon == 7:
                    denom = last_7 if last_7 > 0 else None
                elif horizon == 30:
                    denom = past_30 if past_30 > 0 else None
                else:
                    denom = last_7 if last_7 > 0 else None
                if denom:
                    growth = round((forecast_h - denom) / float(denom) * 100.0, 1)
                else:
                    growth = 0.0

                price = float(p.price) if p.price is not None else 0.0
                projected_revenue = round(forecast_h * price, 2)

                in_stock = p.inventory_items.filter(quantity__gt=0).exists()
                products_payload.append({
                    'product_id': p.id,
                    'product': p.name,
                    'forecast_h': forecast_h,
                    'confidence': float(hinfo.get('confidence', 0)),
                    'trend': summ.get('trend', 'stable'),
                    'last_7_days': last_7,
                    'past_30_days': past_30,
                    'avg': summ.get('avg', 0.0),
                    'growth_rate': growth,
                    'price': price,
                    'projected_revenue': projected_revenue,
                    'category': p.category or '',
                    'is_active': bool(p.is_active),
                    'in_stock': bool(in_stock)
                })
            except Exception:
                logger.exception('Error computing product summary for product id %s', p.id)
                continue
    except Exception as e:
        logger.exception('Error building product forecast payload: %s', str(e))
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

    # Sort by forecast descending
    products_sorted = sorted(products_payload, key=lambda x: x['forecast_h'], reverse=True)

    # Summary aggregates (respecting filters)
    total_forecast_units = sum(p['forecast_h'] for p in products_sorted)
    total_projected_revenue = round(sum(p['projected_revenue'] for p in products_sorted), 2)

    # Trending: sort by growth_rate descending
    trending_sorted = sorted(products_payload, key=lambda x: x.get('growth_rate', 0.0), reverse=True)

    result = {
        'horizon': horizon,
        'top': products_sorted[:top_n],
        'trending': trending_sorted[:max(10, top_n)],
        'best': products_sorted[0] if products_sorted else None,
        'summary': {
            'total_forecast_units': total_forecast_units,
            'projected_revenue': total_projected_revenue,
            'count': len(products_sorted)
        }
    }

    # If product_id requested, include detailed series and forecasts
    if product_id:
        try:
            pid = int(product_id)
            summ = product_forecast_summary(pid, horizons=(1, 7, 30), lookback_days=180)
            result['product_detail'] = summ
        except Exception:
            result['product_detail'] = None

    return JsonResponse(result)


# Admin: user management (Admin only)
@group_required("Admin")
def admin_user_list(request):
    users = User.objects.all().prefetch_related('groups')
    users_info = []
    for u in users:
        users_info.append({
            'user': u,
            'is_admin': u.groups.filter(name='Admin').exists(),
            'is_cashier': u.groups.filter(name='Cashier').exists(),
        })
    return render(request, 'pages/admin_user_list.html', {'users': users_info})


@group_required("Admin")
def forecast_diag(request):
    """Compact diagnostics for deployed instances so admins can quickly verify data source and counts."""
    logger = logging.getLogger(__name__)
    try:
        # CSV helpers were moved to a separate module to keep runtime forecasts DB-only
        from .services.csv_forecasting import csv_aggregate_series
        from .services.forecasting import aggregate_sales
    except Exception as e:
        logger.exception('Diag import failed: %s', str(e))
        return JsonResponse({'error': 'diagnostics unavailable', 'details': str(e)}, status=500)

    try:
        csv_agg = None
        try:
            csv_agg = csv_aggregate_series(limit=100)
        except Exception:
            csv_agg = None

        if csv_agg and (csv_agg.get('daily') or csv_agg.get('weekly') or csv_agg.get('monthly')):
            src = 'csv'
            daily = csv_agg.get('daily', [])
            weekly = csv_agg.get('weekly', [])
            monthly = csv_agg.get('monthly', [])
        else:
            src = 'db'
            daily = aggregate_sales('daily', lookback=60)
            weekly = aggregate_sales('weekly', lookback=12)
            monthly = aggregate_sales('monthly', lookback=12)

        def first_last(series):
            if not series:
                return {'count': 0, 'first': None, 'last': None}
            return {'count': len(series), 'first': series[0][0], 'last': series[-1][0]}

        payload = {
            'data_source': src,
            'daily': first_last(daily),
            'weekly': first_last(weekly),
            'monthly': first_last(monthly),
            'now': timezone.now().isoformat()
        }
        return JsonResponse(payload)
    except Exception as e:
        logger.exception('Error building diag response: %s', str(e))
        return JsonResponse({'error': 'failed to build diag', 'details': str(e)}, status=500)


@group_required("Admin")
@require_http_methods(["POST"])
def admin_toggle_group(request):
    user_id = request.POST.get('user_id')
    group_name = request.POST.get('group')
    action = request.POST.get('action')  # 'add' or 'remove'
    user = get_object_or_404(User, pk=user_id)
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        messages.error(request, f"Group '{group_name}' does not exist.")
        return redirect('admin_user_list')

    # Perform the requested action
    if action == 'add':
        user.groups.add(group)
        msg = f"Added {user.username} to {group.name}."
        messages.success(request, msg)
    else:
        user.groups.remove(group)
        msg = f"Removed {user.username} from {group.name}."
        messages.success(request, msg)

    # If AJAX request, return JSON for client-side updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'message': msg,
            'user_id': user.id,
            'group': group.name,
            'is_admin': user.groups.filter(name='Admin').exists(),
            'is_cashier': user.groups.filter(name='Cashier').exists(),
        })

    return redirect('admin_user_list')


# Record sales by period (week/month) - Auto-summarize and printable
@group_required("Admin")
def record_sales_period(request):
    """Record sales summary for a week or month with printable option"""
    from datetime import timedelta
    
    if request.method == 'POST':
        # Get period from form and determine action
        period = request.POST.get('period', 'week')
        action = request.POST.get('action', 'view')  # 'view' or 'print'
        
        # Get the date range
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())  # Monday of this week
            end_date = start_date + timedelta(days=6)  # Sunday
        else:  # month
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = start_date.replace(year=today.year + 1, month=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=today.month + 1) - timedelta(days=1)
        
        # Get sales for the period
        sales = Sale.objects.filter(date__gte=start_date, date__lte=end_date)
        
        # Calculate totals
        total_units = sales.aggregate(Sum('units_sold'))['units_sold__sum'] or 0
        total_revenue = sales.aggregate(Sum('revenue'))['revenue__sum'] or 0
        
        # Group by product
        sales_by_product = sales.values('product__name').annotate(
            units=Sum('units_sold'),
            revenue=Sum('revenue')
        ).order_by('-revenue')
        
        context = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_units': total_units,
            'total_revenue': total_revenue,
            'sales_by_product': list(sales_by_product),
            'sales_count': sales.count(),
            'now': timezone.now(),
        }
        
        if action == 'print':
            # Return printable version
            return render(request, 'pages/sales_report_print.html', context)
        else:
            return render(request, 'pages/sales_report.html', context)
    
    return render(request, 'pages/sales_period_form.html')

@group_required("Admin")
def api_record_sales_summary(request):
    """API endpoint to record sales summary and return as JSON for printing"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            period = data.get('period', 'week')  # 'week' or 'month'
            
            from datetime import timedelta
            today = timezone.now().date()
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # month
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = start_date.replace(year=today.year + 1, month=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=today.month + 1) - timedelta(days=1)
            
            sales = Sale.objects.filter(date__gte=start_date, date__lte=end_date)
            
            total_units = sales.aggregate(Sum('units_sold'))['units_sold__sum'] or 0
            total_revenue = sales.aggregate(Sum('revenue'))['revenue__sum'] or 0
            
            sales_by_product = list(sales.values('product__name').annotate(
                units=Sum('units_sold'),
                revenue=Sum('revenue')
            ).order_by('-revenue'))
            
            return JsonResponse({
                'success': True,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_units': total_units,
                'total_revenue': float(total_revenue),
                'sales_by_product': sales_by_product,
                'sales_count': sales.count(),
            })
        except Exception as e:
            logging.error('Error in api_record_sales_summary: %s', str(e))
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Owner: Approve/Reject pending cashier signups
@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_approve(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    try:
        pending = Group.objects.get(name='PendingCashier')
    except Group.DoesNotExist:
        pending = None
    cashier_grp, _ = Group.objects.get_or_create(name='Cashier')
    # Move user from pending to cashier and activate
    if pending:
        user.groups.remove(pending)
    user.groups.add(cashier_grp)
    user.is_active = True
    user.save()
    messages.success(request, f"Approved cashier: {user.username}")
    return redirect('pending_cashiers')


@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_reject(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    # Delete the user (reject)
    username = user.username
    user.delete()
    messages.success(request, f"Rejected and removed user: {username}")
    return redirect('pending_cashiers')

@csrf_exempt
def create_sale(request):
    """API endpoint to create a sale transaction"""
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        logger.warning(f'create_sale: Invalid method {request.method}')
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Check if body is empty
        if not request.body:
            logger.error('create_sale: Empty request body')
            return JsonResponse({'error': 'Empty request body'}, status=400)
        
        data = json.loads(request.body)
        logger.info('create_sale payload: %s', data)
        items = data.get('items', [])
        
        if not items:
            logger.warning('create_sale: No items in cart')
            return JsonResponse({'error': 'No items in cart'}, status=400)
        
        # First, validate all items have sufficient inventory
        for item in items:
            try:
                product = Product.objects.get(pk=item['id'])
                inv = product.inventory_items.first()
                
                if inv and inv.quantity < item['quantity']:
                    logger.warning(f'create_sale: Insufficient inventory for {product.name}')
                    return JsonResponse({'error': f'Insufficient inventory for {product.name}. Available: {inv.quantity}, Requested: {item["quantity"]}'}, status=400)
                
                # Validate quantity is positive
                if item['quantity'] <= 0:
                    logger.warning(f'create_sale: Invalid quantity for {product.name}')
                    return JsonResponse({'error': f'Invalid quantity for {product.name}'}, status=400)
            except Product.DoesNotExist:
                logger.error(f'create_sale: Product not found with id {item["id"]}')
                return JsonResponse({'error': f'Product not found (id: {item["id"]})'}, status=404)
        
        # All validations passed, create sale records for each item
        # Use a small retry for transient DB errors (e.g., SSL decryption failures)
        from django.db import close_old_connections
        from django.db.utils import InterfaceError, DatabaseError

        for item in items:
            product = Product.objects.get(pk=item['id'])
            attempt = 0
            while True:
                try:
                    sale = Sale.objects.create(
                        product=product,
                        units_sold=item['quantity'],
                        revenue=float(item['price']) * item['quantity']
                    )

                    # Update inventory
                    inv = product.inventory_items.first()
                    if inv:
                        inv.quantity -= item['quantity']
                        inv.save()
                        logger.info(f'create_sale: Updated inventory for {product.name}, new qty: {inv.quantity}')

                    # success -> break retry loop
                    break

                except (InterfaceError, DatabaseError) as db_exc:
                    # transient DB error (could be SSL/decryption); attempt to recover once
                    logger.warning('create_sale: DB error on write (attempt %s): %s', attempt + 1, str(db_exc))
                    # Close old connections and retry once
                    try:
                        close_old_connections()
                    except Exception:
                        logger.exception('create_sale: close_old_connections failed')
                    attempt += 1
                    if attempt >= 2:
                        logger.exception('create_sale: DB write failed after retry: %s', str(db_exc))
                        raise
        
        logger.info('create_sale: Sale recorded successfully')
        return JsonResponse({'success': True, 'message': 'Sale recorded successfully'})
    except json.JSONDecodeError as e:
        logger.error('create_sale: JSON decode error: %s', str(e))
        logger.error(f'Request body: {request.body}')
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error('='*60)
        logger.error('UNHANDLED EXCEPTION in create_sale')
        logger.error('Error: %s', str(e))
        logger.error('Traceback:\n%s', traceback.format_exc())
        logger.error('='*60)
        return JsonResponse({'error': f'Server error: {str(e)[:100]}'}, status=500)


# Owner: Approve/Reject pending cashier signups
@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_approve(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    try:
        pending = Group.objects.get(name='PendingCashier')
    except Group.DoesNotExist:
        pending = None
    cashier_grp, _ = Group.objects.get_or_create(name='Cashier')
    # Move user from pending to cashier and activate
    if pending:
        user.groups.remove(pending)
    user.groups.add(cashier_grp)
    user.is_active = True
    user.save()
    messages.success(request, f"Approved cashier: {user.username}")
    return redirect('pending_cashiers')


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_reject(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    # Delete the user (reject)
    username = user.username
    user.delete()
    messages.success(request, f"Rejected and removed user: {username}")
    return redirect('pending_cashiers')

@login_required
def recent_orders_api(request):
    """Return recent sales (last 50 orders) with product details, ordered by most recent first."""
    try:
        # Get the 50 most recent sales, ordered by date (newest first)
        recent_sales = Sale.objects.select_related('product').order_by('-date')[:50]
        
        orders = []
        for sale in recent_sales:
            orders.append({
                'id': sale.id,
                'product_name': sale.product.name,
                'category': sale.product.category,
                'units_sold': sale.units_sold,
                'revenue': float(sale.revenue),
                'date': sale.date.isoformat(),
                'date_formatted': sale.date.strftime('%b %d, %I:%M %p')
            })
        
        return JsonResponse({'success': True, 'orders': orders})
    except Exception as e:
        import traceback
        logger = logging.getLogger(__name__)
        logger.error('Error in recent_orders_api: %s', str(e))
        logger.error('Traceback:\n%s', traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
