CREATE TABLE IF NOT EXISTS products (
    product_id    VARCHAR(64)    PRIMARY KEY,
    name          VARCHAR(255)   NOT NULL,
    unit_price    DECIMAL(10, 2) NOT NULL,
    available_qty INT            NOT NULL,
    reserved_qty  INT            NOT NULL,
    version       BIGINT         DEFAULT 0
);
