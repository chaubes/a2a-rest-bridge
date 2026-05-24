package com.agentcart.notification.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

/** A record of a dispatched (mock) customer notification. */
@Entity
@Table(name = "notification_logs")
public class NotificationLog {

    @Id
    @Column(name = "notification_id")
    private String notificationId;

    @Column(name = "customer_id", nullable = false)
    private String customerId;

    @Column(name = "message", length = 1000, nullable = false)
    private String message;

    @Column(name = "channel", nullable = false)
    private String channel;

    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "sent_at", nullable = false)
    private Instant sentAt;

    protected NotificationLog() {
    }

    public NotificationLog(String notificationId, String customerId, String message, String channel,
                           String status, Instant sentAt) {
        this.notificationId = notificationId;
        this.customerId = customerId;
        this.message = message;
        this.channel = channel;
        this.status = status;
        this.sentAt = sentAt;
    }

    public String getNotificationId() {
        return notificationId;
    }

    public String getCustomerId() {
        return customerId;
    }

    public String getMessage() {
        return message;
    }

    public String getChannel() {
        return channel;
    }

    public String getStatus() {
        return status;
    }

    public Instant getSentAt() {
        return sentAt;
    }
}
