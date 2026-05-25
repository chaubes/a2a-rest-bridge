package com.agentcart.inventory.exception;

/** Raised when a requested product does not exist in inventory. */
public class ProductNotFoundException extends RuntimeException {

    public ProductNotFoundException(String productId) {
        super("Product not found: " + productId);
    }
}
