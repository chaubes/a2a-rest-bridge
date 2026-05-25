package com.agentcart.shipping.web;

import com.agentcart.common.dto.ApiError;
import com.agentcart.common.web.AbstractGlobalExceptionHandler;
import com.agentcart.shipping.exception.ShipmentNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Translates shipping-specific exceptions into the shared {@link ApiError} contract. */
@RestControllerAdvice
public class GlobalExceptionHandler extends AbstractGlobalExceptionHandler {

    @ExceptionHandler(ShipmentNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(ShipmentNotFoundException ex) {
        return build(HttpStatus.NOT_FOUND, "Not Found", ex.getMessage());
    }
}
