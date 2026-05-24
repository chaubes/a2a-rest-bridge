package com.agentcart.notification.service;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.notification.domain.NotificationLog;
import com.agentcart.notification.dto.NotificationLogResponse;
import com.agentcart.notification.dto.SendNotificationRequest;
import com.agentcart.notification.dto.SendNotificationResponse;
import com.agentcart.notification.repository.NotificationLogRepository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Mock notification dispatch. Records every notification to the console and the
 * persistent log, then reports it as sent.
 */
@Service
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);
    private static final String SERVICE_NAME = "notification-service";

    private final NotificationLogRepository repository;
    private final AuditLogger auditLogger;

    public NotificationService(NotificationLogRepository repository, AuditLogger auditLogger) {
        this.repository = repository;
        this.auditLogger = auditLogger;
    }

    @Transactional
    public SendNotificationResponse send(SendNotificationRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        String notificationId = "ntf-" + UUID.randomUUID().toString().substring(0, 8);
        log.info("Dispatching {} notification {} to customer {}",
                request.channel(), notificationId, request.customerId());

        NotificationLog entry = new NotificationLog(
                notificationId, request.customerId(), request.message(), request.channel(),
                "SENT", Instant.now());
        NotificationLog saved = repository.save(entry);

        SendNotificationResponse response = new SendNotificationResponse(
                saved.getNotificationId(), saved.getStatus(), saved.getChannel());
        auditLogger.log(SERVICE_NAME, "notification.send", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional(readOnly = true)
    public List<NotificationLogResponse> recentLogs() {
        return repository.findTop50ByOrderBySentAtDesc().stream()
                .map(entry -> new NotificationLogResponse(
                        entry.getNotificationId(), entry.getCustomerId(), entry.getMessage(),
                        entry.getChannel(), entry.getStatus(), entry.getSentAt()))
                .toList();
    }
}
