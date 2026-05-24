package com.agentcart.order.dto;

import java.math.BigDecimal;
import java.time.Instant;

/** Full view of an order. */
public record OrderResponse(
        String orderId,
        String customerId,
        String productId,
        Integer quantity,
        BigDecimal totalAmount,
        String currency,
        String transactionId,
        String trackingId,
        String status,
        Instant createdAt) {
}
