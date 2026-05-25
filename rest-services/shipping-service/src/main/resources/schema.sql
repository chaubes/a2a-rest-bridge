CREATE TABLE IF NOT EXISTS shipments (
    tracking_id        VARCHAR(64)  PRIMARY KEY,
    order_id           VARCHAR(64)  NOT NULL,
    address_line1      VARCHAR(255) NOT NULL,
    city               VARCHAR(128) NOT NULL,
    state              VARCHAR(128) NOT NULL,
    postcode           VARCHAR(32)  NOT NULL,
    country            VARCHAR(128) NOT NULL,
    shipping_method    VARCHAR(32)  NOT NULL,
    status             VARCHAR(32)  NOT NULL,
    estimated_delivery DATE         NOT NULL,
    created_at         TIMESTAMP    NOT NULL
);
