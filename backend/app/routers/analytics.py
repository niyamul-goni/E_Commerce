"""
FashionHub — Analytics Router
Endpoints: Revenue, CLV, Best Sellers, Monthly Sales, Supplier Performance
All queries use PostgreSQL views and materialized views for performance
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth.dependencies import require_admin

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Reports"],
    dependencies=[Depends(require_admin)],
)


@router.get("/dashboard/kpis")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Executive KPI dashboard: total revenue, orders, customers, avg order value.
    Runs Q100 from the query library.
    """
    result = db.execute(text("""
        SELECT
            COUNT(DISTINCT c.id)                                                    AS total_customers,
            COUNT(DISTINCT o.id) FILTER (WHERE o.status != 'cancelled')            AS total_orders,
            COALESCE(SUM(o.total_amount) FILTER (WHERE o.status != 'cancelled'), 0) AS total_revenue,
            ROUND(COALESCE(AVG(o.total_amount) FILTER (WHERE o.status != 'cancelled'), 0), 2) AS avg_order_value,
            COUNT(DISTINCT o.id) FILTER (
                WHERE o.status != 'cancelled'
                  AND o.order_date >= NOW() - INTERVAL '30 days'
            )                                                                       AS orders_last_30d,
            COALESCE(SUM(o.total_amount) FILTER (
                WHERE o.status != 'cancelled'
                  AND o.order_date >= NOW() - INTERVAL '30 days'
            ), 0)                                                                   AS revenue_last_30d,
            COUNT(DISTINCT CASE WHEN o.status = 'pending' THEN o.id END)           AS pending_orders,
            COUNT(DISTINCT rr.id) FILTER (WHERE rr.status = 'pending')             AS pending_returns
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
        LEFT JOIN return_requests rr ON rr.order_id = o.id
    """)).mappings().one()
    return dict(result)


@router.get("/revenue/monthly")
def monthly_revenue(
    months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db)
):
    """Return a complete monthly series, including months without sales."""
    rows = db.execute(text("""
        WITH month_axis AS (
            SELECT generate_series(
                date_trunc('month', CURRENT_DATE)
                    - (:months - 1) * INTERVAL '1 month',
                date_trunc('month', CURRENT_DATE),
                INTERVAL '1 month'
            ) AS month_start
        )
        SELECT
            to_char(axis.month_start, 'YYYY-MM') AS month_label,
            COALESCE(sales.order_count, 0) AS order_count,
            COALESCE(sales.unique_customers, 0) AS unique_customers,
            COALESCE(sales.total_revenue, 0) AS total_revenue,
            COALESCE(sales.total_discounts, 0) AS total_discounts,
            COALESCE(sales.avg_order_value, 0) AS avg_order_value,
            COALESCE(sales.delivered_orders, 0) AS delivered_orders,
            COALESCE(sales.cancelled_orders, 0) AS cancelled_orders,
            sales.mom_growth_pct
        FROM month_axis axis
        LEFT JOIN monthly_sales_view sales
          ON to_date(sales.month_label || '-01', 'YYYY-MM-DD')
             = axis.month_start::date
        ORDER BY axis.month_start DESC
    """), {"months": months}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/revenue/by-brand")
def revenue_by_brand(db: Session = Depends(get_db)):
    """Revenue breakdown by brand (uses revenue_by_brand_view)."""
    rows = db.execute(text(
        "SELECT * FROM revenue_by_brand_view LIMIT 20"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/revenue/by-category")
def revenue_by_category(db: Session = Depends(get_db)):
    """Revenue breakdown by category (uses revenue_by_category_view)."""
    rows = db.execute(text(
        "SELECT * FROM revenue_by_category_view"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/best-selling")
def best_selling_products(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Top-selling products (90 days) from best_selling_products_view."""
    rows = db.execute(text(f"""
        SELECT product_id, product_name, brand_name, category_name,
               total_units_sold, total_revenue, order_count, avg_selling_price
        FROM best_selling_products_view
        LIMIT {limit}
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/top-rated")
def top_rated_products(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Top-rated products with minimum review count threshold."""
    rows = db.execute(text(f"""
        SELECT * FROM top_rated_products_view LIMIT {limit}
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/sales-summary")
def product_sales_summary(db: Session = Depends(get_db)):
    """Pre-computed product sales summary from materialized view (fast)."""
    rows = db.execute(text("""
        SELECT product_id, product_name, brand_name, category_name,
               total_units_sold, total_revenue, avg_rating, review_count,
               total_available_stock, last_refreshed
        FROM mat_product_sales_summary
        ORDER BY total_revenue DESC
        LIMIT 50
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.post("/products/refresh-materialized-views", status_code=200)
def refresh_materialized_views(db: Session = Depends(get_db)):
    """Refresh all materialized views (admin operation)."""
    try:
        db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_product_sales_summary"))
        db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_daily_revenue"))
        db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_inventory_health"))
        db.commit()
        return {"message": "All materialized views refreshed successfully"}
    except Exception as e:
        db.rollback()
        return {"message": f"Refresh failed: {str(e)}"}


@router.get("/customers/lifetime-value")
def customer_lifetime_value(
    limit: int = Query(20, le=100),
    segment: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """CLV ranking with customer segments (Platinum/Gold/Silver/Bronze)."""
    sql = "SELECT * FROM customer_lifetime_value_view"
    if segment:
        sql += f" WHERE customer_segment = :segment"
    sql += f" ORDER BY ltv_rank LIMIT {limit}"

    params = {"segment": segment} if segment else {}
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/coupons/performance")
def coupon_performance(db: Session = Depends(get_db)):
    """Coupon usage analytics: redemption rate, revenue, discount given."""
    rows = db.execute(text(
        "SELECT * FROM coupon_performance_view LIMIT 50"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/suppliers/performance")
def supplier_performance(db: Session = Depends(get_db)):
    """Supplier KPIs: product count, revenue, units sold, reliability."""
    rows = db.execute(text(
        "SELECT * FROM supplier_performance_view LIMIT 20"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/returns/analysis")
def return_analysis(db: Session = Depends(get_db)):
    """Return rate by product (identifies quality issues)."""
    rows = db.execute(text(
        "SELECT * FROM return_analysis_view LIMIT 50"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/revenue/daily")
def daily_revenue_snapshot(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Daily revenue from materialized view."""
    rows = db.execute(text(f"""
        SELECT revenue_date, order_count, unique_customers,
               total_revenue, avg_order_value, last_refreshed
        FROM mat_daily_revenue
        WHERE revenue_date >= NOW()::DATE - {days}
        ORDER BY revenue_date DESC
    """)).mappings().all()
    return [dict(r) for r in rows]
