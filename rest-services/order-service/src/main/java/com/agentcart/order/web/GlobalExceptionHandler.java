package com.agentcart.order.web;

import com.agentcart.common.dto.ApiError;
import com.agentcart.common.web.AbstractGlobalExceptionHandler;
import com.agentcart.order.exception.OrderNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Translates order-specific exceptions into the shared {@link ApiError} contract. */
@RestControllerAdvice
public class GlobalExceptionHandler extends AbstractGlobalExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(OrderNotFoundException ex) {
        return build(HttpStatus.NOT_FOUND, "Not Found", ex.getMessage());
    }
}
