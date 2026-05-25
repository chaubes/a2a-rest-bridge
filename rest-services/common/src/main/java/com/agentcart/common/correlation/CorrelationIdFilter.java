package com.agentcart.common.correlation;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Reads (or generates) a correlation identifier for every inbound request and makes
 * it available through the SLF4J {@link MDC}, a request attribute, and the response
 * header. This lets a single logical operation be traced across the whole platform.
 */
@Component
@Order(CorrelationIdFilter.FILTER_ORDER)
public class CorrelationIdFilter extends OncePerRequestFilter {

    public static final int FILTER_ORDER = Integer.MIN_VALUE + 10;
    public static final String HEADER_NAME = "X-Correlation-ID";
    public static final String MDC_KEY = "correlationId";
    public static final String REQUEST_ATTRIBUTE = "correlationId";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String correlationId = request.getHeader(HEADER_NAME);
        if (!StringUtils.hasText(correlationId)) {
            correlationId = "gen-" + UUID.randomUUID().toString().substring(0, 8);
        }

        MDC.put(MDC_KEY, correlationId);
        request.setAttribute(REQUEST_ATTRIBUTE, correlationId);
        response.setHeader(HEADER_NAME, correlationId);

        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_KEY);
        }
    }
}
