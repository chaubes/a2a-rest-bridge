package com.agentcart.payment.dto;

import java.math.BigDecimal;
import java.time.Instant;

/** Result of a successful charge. */
public record ChargeResponse(
        String transactionId,
        String status,
        BigDecimal amount,
        String currency,
        Instant timestamp) {
}
