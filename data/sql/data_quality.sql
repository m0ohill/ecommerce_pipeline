
-- retail pipeline: PostgreSQL dq Checks

-- general data quality
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE invoice IS NULL) AS null_invoices,
    COUNT(*) FILTER (WHERE stock_code IS NULL) AS null_products,
    COUNT(*) FILTER (WHERE invoice_date IS NULL) AS null_dates,
    COUNT(*) FILTER (WHERE quantity = 0) AS zero_quantities,
    COUNT(*) FILTER (
        WHERE ABS(total_amount - quantity * price) > 0.01
    ) AS incorrect_totals
FROM retail_transactions;

-- business rule validation
SELECT
    COUNT(*) FILTER (
        WHERE price < 0
          AND transaction_type IS DISTINCT FROM 'adjustment'
    ) AS unexpected_negative_prices,
    COUNT(*) FILTER (
        WHERE price < 0
          AND transaction_type = 'adjustment'
    ) AS negative_price_adjustments,
    COUNT(*) FILTER (
        WHERE transaction_type = 'sale'
          AND (quantity <= 0 OR quantity IS NULL)
    ) AS invalid_sale_quantities
FROM retail_transactions;

-- transaction type distribution
SELECT
    transaction_type,
    COUNT(*) AS record_count,
    ROUND(SUM(total_amount), 2) AS total_amount
FROM retail_transactions
GROUP BY transaction_type
ORDER BY record_count DESC;

-- check duplicate source identifiers
SELECT source_file, source_row, COUNT(*)
FROM retail_transactions
GROUP BY source_file, source_row
HAVING COUNT(*) > 1;
