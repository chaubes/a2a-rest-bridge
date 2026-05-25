package com.agentcart.inventory.web;

import com.agentcart.common.dto.ApiError;
import com.agentcart.common.web.AbstractGlobalExceptionHandler;
import com.agentcart.inventory.exception.InsufficientStockException;
import com.agentcart.inventory.exception.ProductNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Translates inventory-specific exceptions into the shared {@link ApiError} contract. */
@RestControllerAdvice
public class GlobalExceptionHandler extends AbstractGlobalExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(ProductNotFoundException ex) {
        return build(HttpStatus.NOT_FOUND, "Not Found", ex.getMessage());
    }

    @ExceptionHandler(InsufficientStockException.class)
    public ResponseEntity<ApiError> handleInsufficientStock(InsufficientStockException ex) {
        return build(HttpStatus.CONFLICT, "Insufficient Stock", ex.getMessage());
    }
}
