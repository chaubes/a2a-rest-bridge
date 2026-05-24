package com.agentcart.inventory.exception;

/** Raised when a reservation cannot be fulfilled because available stock is too low. */
public class InsufficientStockException extends RuntimeException {

    public InsufficientStockException(String productId, int requested, int available) {
        super("Insufficient stock for " + productId + ": requested " + requested + ", available " + available);
    }
}
