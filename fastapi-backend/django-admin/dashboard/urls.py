from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    # =====================================================
    # ORDER REPORTS
    # =====================================================

    path(
        "reports/orders/csv/",
        views.export_orders_csv,
        name="export_orders_csv",
    ),

    path(
        "reports/orders/pdf/",
        views.export_orders_pdf,
        name="export_orders_pdf",
    ),

    # =====================================================
    # SALES REPORTS
    # =====================================================

    path(
        "reports/sales/csv/",
        views.export_sales_csv,
        name="export_sales_csv",
    ),

    path(
        "reports/sales/pdf/",
        views.export_sales_pdf,
        name="export_sales_pdf",
    ),

    # =====================================================
    # USER REPORTS
    # =====================================================

    path(
        "reports/users/csv/",
        views.export_users_csv,
        name="export_users_csv",
    ),

    path(
        "reports/users/pdf/",
        views.export_users_pdf,
        name="export_users_pdf",
    ),
]