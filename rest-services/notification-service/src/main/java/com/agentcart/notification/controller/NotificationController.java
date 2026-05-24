package com.agentcart.notification.controller;

import com.agentcart.notification.dto.NotificationLogResponse;
import com.agentcart.notification.dto.SendNotificationRequest;
import com.agentcart.notification.dto.SendNotificationResponse;
import com.agentcart.notification.service.NotificationService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** REST endpoints for sending notifications and reading the notification log. */
@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {

    private final NotificationService notificationService;

    public NotificationController(NotificationService notificationService) {
        this.notificationService = notificationService;
    }

    @PostMapping
    public ResponseEntity<SendNotificationResponse> send(@Valid @RequestBody SendNotificationRequest request) {
        return ResponseEntity.ok(notificationService.send(request));
    }

    @GetMapping("/log")
    public List<NotificationLogResponse> log() {
        return notificationService.recentLogs();
    }
}
