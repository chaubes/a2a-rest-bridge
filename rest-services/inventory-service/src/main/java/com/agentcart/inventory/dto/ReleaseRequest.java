package com.agentcart.inventory.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

/** Request to release a previously reserved quantity of a product. */
public record ReleaseRequest(
        @NotBlank String productId,
        @NotNull @Positive @Max(9999) Integer quantity,
        @NotBlank String correlationId) {
}
