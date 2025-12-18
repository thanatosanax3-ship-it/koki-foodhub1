from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="auth_signup"),
    # Products
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_update, name="product_update"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:product_id>/image/", views.product_image, name="product_image"),
    # Inventory
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inventory/create/", views.inventory_create, name="inventory_create"),
    path("inventory/<int:pk>/edit/", views.inventory_update, name="inventory_update"),
    path("inventory/<int:pk>/delete/", views.inventory_delete, name="inventory_delete"),
    # Sales
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/create/", views.sale_create, name="sale_create"),
    path("sales/api/create/", views.create_sale, name="api_create_sale"),
    path("sales/<int:pk>/edit/", views.sale_update, name="sale_update"),
    path("sales/<int:pk>/delete/", views.sale_delete, name="sale_delete"),
    path("sales-dashboard/", views.sales_dashboard, name="sales_dashboard"),
    path("api/sales/today/", views.sales_today_api, name="api_sales_today"),
    path("api/sales/recent/", views.recent_orders_api, name="api_recent_orders"),
    path("sales/period/", views.record_sales_period, name="record_sales_period"),
    path("api/sales/summary/", views.api_record_sales_summary, name="api_sales_summary"),
    # Forecast
    path("forecast/", views.forecast_view, name="forecast"),
    path("forecast/api/", views.forecast_data_api, name="forecast_api"),
    path("product-forecast/", views.product_forecast, name="product_forecast"),
    path("product-forecast/api/", views.product_forecast_api, name="product_forecast_api"),
    path("forecast/diag/", views.forecast_diag, name="forecast_diag"),
    # Lightweight health check endpoint
    path("healthz/", views.healthz, name="healthz"),
    # User management (avoid colliding with Django admin URL prefix)
    path("users/manage/", views.admin_user_list, name="admin_user_list"),
    path("users/manage/toggle/", views.admin_toggle_group, name="admin_toggle_group"),
    path("users/pending/", views.pending_cashiers, name="pending_cashiers"),
    path("users/pending/approve/", views.pending_cashier_approve, name="pending_cashier_approve"),
    path("users/pending/reject/", views.pending_cashier_reject, name="pending_cashier_reject"),
    # Auth
    # Logout handled at project urls to centralize auth routes
]
