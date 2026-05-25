package com.agentcart.order.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import java.math.BigDecimal;

/** Request to create a confirmed order. */
public record CreateOrderRequest(
        @NotBlank String customerId,
        @NotBlank String productId,
        @NotNull @Positive @Max(9999) Integer quantity,
        @NotNull @Positive BigDecimal totalAmount,
        @NotBlank @Pattern(regexp = "^(AUD|USD|EUR|GBP)$") String currency,
        @NotBlank String transactionId,
        @NotBlank String trackingId,
        @NotBlank String correlationId) {
}
