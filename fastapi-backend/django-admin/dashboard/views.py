from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.http import HttpResponse

import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from .models import User, Product, Order, OrderItem, Payment


# =========================================================
# DASHBOARD
# =========================================================
@staff_member_required
def dashboard(request):

    # =====================================================
    # BASIC STATISTICS
    # =====================================================

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()

    # =====================================================
    # TOTAL REVENUE
    # =====================================================

    revenue = (
        Payment.objects
        .filter(status="completed")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # =====================================================
    # ORDER STATUS
    # =====================================================

    order_status_data = (
        Order.objects
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    order_status_labels = [
        item["status"]
        for item in order_status_data
    ]

    order_status_counts = [
        item["count"]
        for item in order_status_data
    ]

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status_data = (
        Payment.objects
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    payment_status_labels = [
        item["status"]
        for item in payment_status_data
    ]

    payment_status_counts = [
        item["count"]
        for item in payment_status_data
    ]

    # =====================================================
    # REVENUE TRENDS
    # =====================================================

    revenue_data = (
        Payment.objects
        .filter(status="completed")
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    revenue_labels = [
        item["date"].strftime("%d-%m-%Y")
        for item in revenue_data
        if item["date"] is not None
    ]

    revenue_values = [
        float(item["total"] or 0)
        for item in revenue_data
        if item["date"] is not None
    ]

    # =====================================================
    # TOP-SELLING PRODUCTS
    # =====================================================

    top_selling_products = (
        OrderItem.objects
        .filter(order__payment__status="completed")
        .values(
            "product__id",
            "product__name",
        )
        .annotate(
            total_quantity=Sum("quantity"),
            total_sales=Sum(
                ExpressionWrapper(
                    F("quantity") * F("price"),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2,
                    ),
                )
            ),
        )
        .order_by("-total_quantity")[:10]
    )

    top_product_labels = [
        item["product__name"]
        for item in top_selling_products
    ]

    top_product_quantities = [
        item["total_quantity"] or 0
        for item in top_selling_products
    ]

    top_product_sales = [
        float(item["total_sales"] or 0)
        for item in top_selling_products
    ]

    # =====================================================
    # LOW STOCK ALERTS
    # =====================================================

    LOW_STOCK_THRESHOLD = 10

    low_stock_products = (
        Product.objects
        .filter(stock__lte=LOW_STOCK_THRESHOLD)
        .order_by("stock", "name")
    )

    # =====================================================
    # RECENT ORDERS
    # =====================================================

    recent_orders = (
        Order.objects
        .select_related("user", "payment")
        .order_by("-created_at")[:10]
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "revenue": revenue,

        "order_status_labels": order_status_labels,
        "order_status_counts": order_status_counts,

        "payment_status_labels": payment_status_labels,
        "payment_status_counts": payment_status_counts,

        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,

        "top_product_labels": top_product_labels,
        "top_product_quantities": top_product_quantities,
        "top_product_sales": top_product_sales,

        "low_stock_products": low_stock_products,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,

        "recent_orders": recent_orders,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


# =========================================================
# EXPORT ORDERS - CSV
# =========================================================
@staff_member_required
def export_orders_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "Customer",
        "Total Amount",
        "Order Status",
        "Payment Status",
        "Created At",
    ])

    orders = (
        Order.objects
        .select_related("user", "payment")
        .order_by("-created_at")
    )

    for order in orders:

        try:
            payment_status = order.payment.status
        except Payment.DoesNotExist:
            payment_status = "N/A"

        writer.writerow([
            order.id,
            str(order.user),
            order.total_amount,
            order.status,
            payment_status,
            order.created_at.strftime(
                "%d-%m-%Y %H:%M"
            ),
        ])

    return response


# =========================================================
# EXPORT ORDERS - PDF
# =========================================================
@staff_member_required
def export_orders_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            "Smart E-Commerce - Orders Report",
            styles["Title"],
        )
    )

    elements.append(Spacer(1, 20))

    orders = (
        Order.objects
        .select_related("user", "payment")
        .order_by("-created_at")
    )

    data = [[
        "Order ID",
        "Customer",
        "Amount",
        "Order Status",
        "Payment Status",
        "Date",
    ]]

    for order in orders:

        try:
            payment_status = order.payment.status
        except Payment.DoesNotExist:
            payment_status = "N/A"

        data.append([
            f"#{order.id}",
            str(order.user),
            f"Rs. {order.total_amount}",
            str(order.status),
            payment_status,
            order.created_at.strftime(
                "%d-%m-%Y %H:%M"
            ),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            60,
            150,
            90,
            100,
            100,
            110,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, 0),
                8,
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response


# =========================================================
# EXPORT SALES - CSV
# =========================================================
@staff_member_required
def export_sales_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="sales_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Payment ID",
        "Order ID",
        "Customer",
        "Amount",
        "Payment Method",
        "Payment Status",
        "Transaction ID",
        "Created At",
    ])

    payments = (
        Payment.objects
        .filter(status="completed")
        .select_related("order", "order__user")
        .order_by("-created_at")
    )

    for payment in payments:

        writer.writerow([
            payment.id,
            payment.order_id,
            str(payment.order.user),
            payment.amount,
            payment.payment_method,
            payment.status,
            payment.transaction_id or "N/A",
            payment.created_at.strftime(
                "%d-%m-%Y %H:%M"
            ),
        ])

    return response


# =========================================================
# EXPORT SALES - PDF
# =========================================================
@staff_member_required
def export_sales_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="sales_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            "Smart E-Commerce - Sales Report",
            styles["Title"],
        )
    )

    elements.append(Spacer(1, 20))

    payments = (
        Payment.objects
        .filter(status="completed")
        .select_related("order", "order__user")
        .order_by("-created_at")
    )

    data = [[
        "Payment ID",
        "Order ID",
        "Customer",
        "Amount",
        "Method",
        "Transaction ID",
        "Date",
    ]]

    for payment in payments:

        data.append([
            payment.id,
            f"#{payment.order_id}",
            str(payment.order.user),
            f"Rs. {payment.amount}",
            payment.payment_method,
            payment.transaction_id or "N/A",
            payment.created_at.strftime(
                "%d-%m-%Y %H:%M"
            ),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            60,
            60,
            140,
            80,
            80,
            150,
            100,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response


# =========================================================
# EXPORT USERS - CSV
# =========================================================
@staff_member_required
def export_users_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="users_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "User ID",
        "Name",
        "Email",
        "Role",
        "Active",
        "Created At",
    ])

    users = User.objects.order_by("-created_at")

    for user in users:

        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.role,
            "Active" if user.is_active else "Inactive",
            (
                user.created_at.strftime("%d-%m-%Y %H:%M")
                if user.created_at
                else "N/A"
            ),
        ])

    return response


# =========================================================
# EXPORT USERS - PDF
# =========================================================
@staff_member_required
def export_users_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="users_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            "Smart E-Commerce - Users Report",
            styles["Title"],
        )
    )

    elements.append(Spacer(1, 20))

    users = User.objects.order_by("-created_at")

    data = [[
        "User ID",
        "Name",
        "Email",
        "Role",
        "Status",
        "Created At",
    ]]

    for user in users:

        data.append([
            user.id,
            user.name,
            user.email,
            user.role,
            "Active" if user.is_active else "Inactive",
            (
                user.created_at.strftime("%d-%m-%Y %H:%M")
                if user.created_at
                else "N/A"
            ),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            60,
            120,
            190,
            80,
            80,
            120,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
        ])
    )

    elements.append(table)
    document.build(elements)
    return response
