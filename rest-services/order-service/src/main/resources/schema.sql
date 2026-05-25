CREATE TABLE IF NOT EXISTS orders (
    order_id       VARCHAR(64)    PRIMARY KEY,
    customer_id    VARCHAR(128)   NOT NULL,
    product_id     VARCHAR(64)    NOT NULL,
    quantity       INT            NOT NULL,
    total_amount   DECIMAL(12, 2) NOT NULL,
    currency       VARCHAR(3)     NOT NULL,
    transaction_id VARCHAR(64),
    tracking_id    VARCHAR(64),
    status         VARCHAR(32)    NOT NULL,
    created_at     TIMESTAMP      NOT NULL
);
