package com.agentcart.notification.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** Request to dispatch a notification to a customer. */
public record SendNotificationRequest(
        @NotBlank String customerId,
        @NotBlank @Size(max = 1000) String message,
        @Pattern(regexp = "^(email|sms)$") String channel,
        @NotBlank String correlationId) {
}
