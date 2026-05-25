package com.agentcart.shipping.exception;

/** Raised when a requested shipment cannot be found. */
public class ShipmentNotFoundException extends RuntimeException {

    public ShipmentNotFoundException(String trackingId) {
        super("Shipment not found: " + trackingId);
    }
}
