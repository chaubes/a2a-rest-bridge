package com.agentcart.shipping.dto;

import java.time.LocalDate;

/** Result of creating a shipment. */
public record CreateShipmentResponse(
        String trackingId,
        String orderId,
        String status,
        LocalDate estimatedDelivery,
        String shippingMethod) {
}
