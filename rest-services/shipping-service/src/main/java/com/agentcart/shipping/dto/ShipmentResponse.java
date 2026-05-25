package com.agentcart.shipping.dto;

import java.time.Instant;
import java.time.LocalDate;

/** Full view of a shipment. */
public record ShipmentResponse(
        String trackingId,
        String orderId,
        String addressLine1,
        String city,
        String state,
        String postcode,
        String country,
        String shippingMethod,
        String status,
        LocalDate estimatedDelivery,
        Instant createdAt) {
}
