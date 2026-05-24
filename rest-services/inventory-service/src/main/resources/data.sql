MERGE INTO products (product_id, name, unit_price, available_qty, reserved_qty, version) KEY (product_id) VALUES
    ('WB-001', 'Blue Widget',            14.99, 100, 0, 0),
    ('WB-002', 'Red Widget',             12.99,  50, 0, 0),
    ('WR-001', 'Widget Rack',            49.99,  25, 0, 0),
    ('WH-001', 'Widget Holder',           7.99, 200, 0, 0),
    ('WS-001', 'Widget Set (Assorted)',  39.99,  30, 0, 0);
