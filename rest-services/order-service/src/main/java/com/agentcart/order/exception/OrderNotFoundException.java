package com.agentcart.order.exception;

/** Raised when a requested order does not exist. */
public class OrderNotFoundException extends RuntimeException {

    public OrderNotFoundException(String orderId) {
        super("Order not found: " + orderId);
    }
}
