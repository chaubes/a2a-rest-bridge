package com.agentcart.notification.dto;

/** Result of dispatching a notification. */
public record SendNotificationResponse(
        String notificationId,
        String status,
        String channel) {
}
