-- 1. Общие показатели магазина

SELECT
    COUNT(DISTINCT order_id) AS orders_count,
    COUNT(DISTINCT customer_id) AS customers_count,
    SUM(revenue) AS total_revenue,
    SUM(cost) AS total_cost,
    SUM(profit) AS total_profit,
    ROUND(
        SUM(profit) / NULLIF(SUM(revenue), 0) * 100,
        2
    ) AS margin_percent
FROM sales_report
WHERE order_status = 'Завершён';


-- 2. Продажи по категориям

SELECT
    category,
    COUNT(DISTINCT order_id) AS orders_count,
    SUM(quantity) AS products_sold,
    SUM(revenue) AS revenue,
    SUM(profit) AS profit
FROM sales_report
WHERE order_status = 'Завершён'
GROUP BY category
ORDER BY revenue DESC;


-- 3. Продажи по городам

SELECT
    city,
    COUNT(DISTINCT customer_id) AS customers_count,
    COUNT(DISTINCT order_id) AS orders_count,
    SUM(revenue) AS revenue,
    SUM(profit) AS profit
FROM sales_report
WHERE order_status = 'Завершён'
GROUP BY city
ORDER BY revenue DESC;


-- 4. Средний чек

SELECT
    ROUND(
        SUM(revenue)
        / NULLIF(COUNT(DISTINCT order_id), 0),
        2
    ) AS average_order_value
FROM sales_report
WHERE order_status = 'Завершён';
-- 5. Дневные показатели для главной страницы Power BI

WITH daily_metrics AS (
    SELECT
        order_date,

        COUNT(DISTINCT order_id) AS orders_count,
        COUNT(DISTINCT customer_id) AS customers_count,

        SUM(revenue) AS revenue,
        SUM(profit) AS profit,

        ROUND(
            SUM(revenue)
            / NULLIF(COUNT(DISTINCT order_id), 0),
            2
        ) AS average_order_value

    FROM sales_report

    WHERE order_status = 'Завершён'

    GROUP BY order_date
)

SELECT
    order_date,
    orders_count,
    customers_count,
    revenue,
    profit,
    average_order_value,

    LAG(orders_count) OVER (
        ORDER BY order_date
    ) AS previous_orders_count,

    LAG(customers_count) OVER (
        ORDER BY order_date
    ) AS previous_customers_count,

    LAG(revenue) OVER (
        ORDER BY order_date
    ) AS previous_revenue,

    LAG(profit) OVER (
        ORDER BY order_date
    ) AS previous_profit,

    LAG(average_order_value) OVER (
        ORDER BY order_date
    ) AS previous_average_order_value
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
) AS orders_change_percent

FROM daily_metrics

ORDER BY order_date;