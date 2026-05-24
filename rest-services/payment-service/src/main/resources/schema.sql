CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(64)    PRIMARY KEY,
    customer_id    VARCHAR(128)   NOT NULL,
    amount         DECIMAL(12, 2) NOT NULL,
    currency       VARCHAR(3)     NOT NULL,
    status         VARCHAR(32)    NOT NULL,
    timestamp      TIMESTAMP      NOT NULL
);
