package com.agentcart.common.audit;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Emits a structured, single-line JSON audit record to stdout for every
 * state-mutating REST operation. Each record is tagged {@code layer:"rest"} so it can
 * be distinguished from audit entries produced by other layers of the platform.
 */
@Component
public class AuditLogger {

    private static final Logger log = LoggerFactory.getLogger(AuditLogger.class);

    private final ObjectMapper objectMapper;

    public AuditLogger(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * Serializes and logs a single audit entry.
     *
     * @param service       logical name of the emitting service
     * @param action        the operation being recorded (e.g. {@code "stock.reserve"})
     * @param correlationId correlation id threading the operation across layers
     * @param request       request payload (any JSON-serializable object)
     * @param response      response payload (any JSON-serializable object)
     * @param durationMs     wall-clock duration of the operation in milliseconds
     */
    public void log(String service, String action, String correlationId,
                    Object request, Object response, long durationMs) {
        Map<String, Object> entry = new LinkedHashMap<>();
        entry.put("layer", "rest");
        entry.put("timestamp", Instant.now().toString());
        entry.put("service", service);
        entry.put("action", action);
        entry.put("correlationId", correlationId);
        entry.put("request", request);
        entry.put("response", response);
        entry.put("durationMs", durationMs);

        try {
            log.info(objectMapper.writeValueAsString(entry));
        } catch (JsonProcessingException ex) {
            log.warn("Unable to serialize audit entry for service={} action={}", service, action, ex);
        }
    }
}
