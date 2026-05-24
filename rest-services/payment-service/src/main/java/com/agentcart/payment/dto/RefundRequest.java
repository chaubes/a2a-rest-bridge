package com.agentcart.payment.dto;

import jakarta.validation.constraints.NotBlank;

/** Request to refund a previously recorded transaction. */
public record RefundRequest(
        @NotBlank String transactionId,
        @NotBlank String correlationId) {
}
