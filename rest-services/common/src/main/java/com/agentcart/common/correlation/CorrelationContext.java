package com.agentcart.common.correlation;

import org.slf4j.MDC;
import org.springframework.util.StringUtils;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * Convenience accessor for the current request's correlation identifier. Falls back
 * to the MDC value and finally to a literal {@code "unknown"} when no request is bound.
 */
public final class CorrelationContext {

    private CorrelationContext() {
    }

    /**
     * Resolves the active correlation id, preferring the request attribute set by
     * {@link CorrelationIdFilter} and falling back to the MDC.
     */
    public static String current() {
        if (RequestContextHolder.getRequestAttributes() instanceof ServletRequestAttributes attributes) {
            Object value = attributes.getRequest().getAttribute(CorrelationIdFilter.REQUEST_ATTRIBUTE);
            if (value instanceof String id && StringUtils.hasText(id)) {
                return id;
            }
        }
        String fromMdc = MDC.get(CorrelationIdFilter.MDC_KEY);
        return StringUtils.hasText(fromMdc) ? fromMdc : "unknown";
    }

    /**
     * Resolves a correlation id, preferring a caller-supplied value (e.g. from a request
     * body) and falling back to the request-scoped value when blank.
     */
    public static String resolve(String supplied) {
        return StringUtils.hasText(supplied) ? supplied : current();
    }
}
