package com.agentcart.common.dto;

import java.time.Instant;

/**
 * Standard error payload returned by every REST service in the platform.
 *
 * <p>Field names are serialized as-is (camelCase) so downstream clients can rely
 * on a single, predictable error contract regardless of which service produced it.
 */
public record ApiError(
        String timestamp,
        int status,
        String error,
        String message,
        String path,
        String correlationId) {

    /**
     * Builds an {@link ApiError} stamping the current UTC instant as the timestamp.
     */
    public static ApiError of(int status, String error, String message, String path, String correlationId) {
        return new ApiError(Instant.now().toString(), status, error, message, path, correlationId);
    }
}
