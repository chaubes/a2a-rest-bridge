package com.agentcart.payment.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import java.math.BigDecimal;

/** Request to charge a customer's payment method. */
public record ChargeRequest(
        @NotBlank String customerId,
        @NotNull @Positive @DecimalMax("999999.99") BigDecimal amount,
        @NotBlank @Pattern(regexp = "^(AUD|USD|EUR|GBP)$") String currency,
        @NotBlank String paymentMethodToken,
        @NotBlank String correlationId) {
}
