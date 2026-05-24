package com.agentcart.payment.dto;

/** Result of a refund operation. */
public record RefundResponse(
        String transactionId,
        String status) {
}
