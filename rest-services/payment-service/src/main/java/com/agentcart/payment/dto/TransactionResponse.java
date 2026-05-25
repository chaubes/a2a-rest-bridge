package com.agentcart.payment.dto;

import java.math.BigDecimal;

/** Detail view of a single transaction. */
public record TransactionResponse(
        String transactionId,
        String customerId,
        BigDecimal amount,
        String currency,
        String status) {
}
