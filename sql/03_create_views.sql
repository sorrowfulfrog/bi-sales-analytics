-- Представления для аналитики и Power BI

CREATE OR REPLACE VIEW sales_report AS
SELECT
    o.order_id,
    o.order_date,
    o.order_status,

    c.customer_id,
    c.customer_name,
    c.city,
    c.registration_date,

    p.product_id,
    p.product_name,
    p.category,

    oi.quantity,
    oi.unit_price,
    p.purchase_price,

    oi.quantity * oi.unit_price AS revenue,
    oi.quantity * p.purchase_price AS cost,
    oi.quantity * (
        oi.unit_price - p.purchase_price
    ) AS profit

FROM orders AS o

JOIN customers AS c
    ON c.customer_id = o.customer_id

JOIN order_items AS oi
    ON oi.order_id = o.order_id

JOIN products AS p
    ON p.product_id = oi.product_id;

-- Дневные KPI для Power BI

CREATE OR REPLACE VIEW daily_kpi AS

WITH daily_metrics AS (
    SELECT
        order_date,

        COUNT(DISTINCT order_id) AS orders_count,
        COUNT(DISTINCT customer_id) AS customers_count,

        SUM(quantity) AS products_sold,
        SUM(revenue) AS revenue,
        SUM(cost) AS cost,
        SUM(profit) AS profit,

        ROUND(
            SUM(revenue)
            / NULLIF(COUNT(DISTINCT order_id), 0),
            2
        ) AS average_order_value,

        ROUND(
            SUM(profit)
            / NULLIF(SUM(revenue), 0)
            * 100,
            2
        ) AS margin_percent

    FROM sales_report

    WHERE order_status = 'Завершён'

    GROUP BY order_date
)

SELECT
    order_date,
    orders_count,
    customers_count,
    products_sold,
    revenue,
    cost,
    profit,
    average_order_value,
    margin_percent,

    ROUND(
        (
            revenue
            - LAG(revenue) OVER (ORDER BY order_date)
        )
        / NULLIF(
            LAG(revenue) OVER (ORDER BY order_date),
            0
        )
        * 100,
        2
    ) AS revenue_change_percent,

    ROUND(
        (
            profit
            - LAG(profit) OVER (ORDER BY order_date)
        )
        / NULLIF(
            LAG(profit) OVER (ORDER BY order_date),
            0
        )
        * 100,
        2
    ) AS profit_change_percent,

    ROUND(
        (
            orders_count
            - LAG(orders_count) OVER (ORDER BY order_date)
        )::NUMERIC
        / NULLIF(
            LAG(orders_count) OVER (ORDER BY order_date),
            0
        )
        * 100,
        2
    ) AS orders_change_percent,

    ROUND(
        (
            customers_count
            - LAG(customers_count) OVER (ORDER BY order_date)
        )::NUMERIC
        / NULLIF(
            LAG(customers_count) OVER (ORDER BY order_date),
            0
        )
        * 100,
        2
    ) AS customers_change_percent,

    ROUND(
        (
            average_order_value
            - LAG(average_order_value) OVER (ORDER BY order_date)
        )
        / NULLIF(
            LAG(average_order_value) OVER (ORDER BY order_date),
            0
        )
        * 100,
        2
    ) AS average_order_value_change_percent

FROM daily_metrics;