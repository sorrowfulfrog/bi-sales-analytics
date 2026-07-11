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