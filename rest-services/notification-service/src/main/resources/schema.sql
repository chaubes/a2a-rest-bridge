CREATE TABLE IF NOT EXISTS notification_logs (
    notification_id VARCHAR(64)   PRIMARY KEY,
    customer_id     VARCHAR(128)  NOT NULL,
    message         VARCHAR(1000) NOT NULL,
    channel         VARCHAR(16)   NOT NULL,
    status          VARCHAR(32)   NOT NULL,
    sent_at         TIMESTAMP     NOT NULL
);
