package com.agentcart.shipping.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Request to create a shipment. {@code shippingMethod} is optional and defaults to
 * "standard" when blank, so it carries no {@code @NotBlank} constraint.
 */
public record CreateShipmentRequest(
        @NotBlank String orderId,
        @NotBlank String addressLine1,
        @NotBlank String city,
        @NotBlank String state,
        @NotBlank String postcode,
        @NotBlank String country,
        String shippingMethod,
        @NotBlank String correlationId) {
}
