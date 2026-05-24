package com.agentcart.common.web;

import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.common.dto.ApiError;
import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * Shared exception-handling behaviour that produces the platform-wide {@link ApiError}
 * contract. Each service declares its own {@code @RestControllerAdvice} extending this
 * class so service-specific business exceptions can be added on top of the common cases.
 */
public abstract class AbstractGlobalExceptionHandler {

    /**
     * Bean-validation failures on request bodies map to HTTP 422.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleMethodArgumentNotValid(MethodArgumentNotValidException ex) {
        FieldError fieldError = ex.getBindingResult().getFieldError();
        String detail = fieldError != null
                ? fieldError.getField() + " " + fieldError.getDefaultMessage()
                : "Request validation failed";
        return build(HttpStatus.UNPROCESSABLE_ENTITY, "Validation Failed", detail);
    }

    /**
     * Constraint violations (e.g. on path/query parameters) map to HTTP 422.
     */
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiError> handleConstraintViolation(ConstraintViolationException ex) {
        return build(HttpStatus.UNPROCESSABLE_ENTITY, "Validation Failed", ex.getMessage());
    }

    /**
     * Malformed or missing request bodies map to HTTP 400.
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> handleNotReadable(HttpMessageNotReadableException ex) {
        return build(HttpStatus.BAD_REQUEST, "Bad Request", "Malformed or missing request body");
    }

    /**
     * Catch-all for unexpected failures, returning HTTP 500 without leaking internals.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnexpected(Exception ex) {
        return build(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", "An unexpected error occurred");
    }

    /**
     * Builds a {@link ResponseEntity} carrying the standard error contract.
     */
    protected ResponseEntity<ApiError> build(HttpStatus status, String error, String message) {
        ApiError body = ApiError.of(status.value(), error, message, currentPath(), CorrelationContext.current());
        return ResponseEntity.status(status).body(body);
    }

    /**
     * Resolves the current request path for inclusion in the error contract.
     */
    protected String currentPath() {
        if (RequestContextHolder.getRequestAttributes() instanceof ServletRequestAttributes attributes) {
            return attributes.getRequest().getRequestURI();
        }
        return "";
    }
}
