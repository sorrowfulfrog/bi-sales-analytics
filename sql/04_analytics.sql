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