package com.agentcart.notification.web;

import com.agentcart.common.dto.ApiError;
import com.agentcart.common.web.AbstractGlobalExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Notification service exception handler. It inherits the platform-wide handling
 * (validation, bad request, fallback) and produces the shared {@link ApiError} contract.
 */
@RestControllerAdvice
public class GlobalExceptionHandler extends AbstractGlobalExceptionHandler {
}
