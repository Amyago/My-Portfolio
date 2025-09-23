-- Часть 1: Создание структуры таблицы
-- Создаем таблицу с правильными типами данных
CREATE TABLE new_credits_august_2025 (
    client_id INT PRIMARY KEY,                         -- Уникальный ID клиента, целое число. PRIMARY KEY обеспечивает уникальность.
    credit_product_type VARCHAR(50) NOT NULL,          -- Тип продукта, текстовая строка до 50 символов. Не может быть пустым.
    issue_date DATE NOT NULL,                          -- Дата выдачи, специальный тип DATE. Не может быть пустой.
    first_payment_date DATE NOT NULL,                  -- Плановая дата платежа, тип DATE. Не может быть пустой.
    first_payment_fact_date DATE,                      -- Фактическая дата платежа, тип DATE. МОЖЕТ быть пустой (NULL), если платежа не было.
    initial_credit_score INT,                          -- Скоринговый балл, целое число. Может быть пустым.
    client_segment VARCHAR(50) NOT NULL                -- Сегмент клиента, текстовая строка до 50 символов. Не может быть пустым.
);


-- Часть 2: Наполнение таблицы данными
-- Используем одну команду INSERT для добавления всех 10 строк
INSERT INTO new_credits_august_2025 (client_id, credit_product_type, issue_date, first_payment_date, first_payment_fact_date, initial_credit_score, client_segment) VALUES
(1001, 'Рассрочка', '2025-08-02', '2025-09-02', '2025-09-02', 710, 'Постоянный покупатель'),
(1002, 'Кредитная карта', '2025-08-03', '2025-09-03', '2025-09-01', 780, 'Ozon Premium'),
(1003, 'Рассрочка', '2025-08-05', '2025-09-05', '2025-09-05', 650, 'Постоянный покупатель'),
(1004, 'Рассрочка', '2025-08-08', '2025-09-08', '2025-09-11', 590, 'Новый на Ozon'),
(1005, 'Кредитная карта', '2025-08-11', '2025-09-11', NULL, 450, 'Новый на Ozon'),
(1006, 'Кредитная карта', '2025-08-15', '2025-09-15', '2025-09-14', 810, 'Ozon Premium'),
(1007, 'Рассрочка', '2025-08-19', '2025-09-19', '2025-09-20', 680, 'Постоянный покупатель'),
(1008, 'Рассрочка', '2025-08-22', '2025-09-22', NULL, 510, 'Новый на Ozon'),
(1009, 'Кредитная карта', '2025-08-25', '2025-09-25', '2025-09-25', 730, 'Постоянный покупатель'),
(1010, 'Рассрочка', '2025-08-28', '2025-09-28', '2025-10-02', 550, 'Постоянный покупатель');

SELECT * FROM new_credits_august_2025;

SELECT
    COUNT(*) AS total_clients,
    SUM(CASE WHEN first_payment_fact_date IS NULL THEN 1 ELSE 0 END) AS defaulters_count,
    (SUM(CASE WHEN first_payment_fact_date IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100.0 AS fpd_rate_percent
FROM
    new_credits_august_2025;

SELECT
    client_segment,
    COUNT(*) AS total_clients,
    SUM(CASE WHEN first_payment_fact_date IS NULL THEN 1 ELSE 0 END) AS defaulters_count,
    (SUM(CASE WHEN first_payment_fact_date IS NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100.0 AS fpd_rate_percent
FROM
    new_credits_august_2025
GROUP BY
    client_segment
ORDER BY
    fpd_rate_percent DESC;
