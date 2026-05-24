package com.agentcart.notification.dto;

import java.time.Instant;

/** A single entry in the notification log. */
public record NotificationLogResponse(
        String notificationId,
        String customerId,
        String message,
        String channel,
        String status,
        Instant sentAt) {
}
