package com.agentcart.payment.web;

import com.agentcart.common.dto.ApiError;
import com.agentcart.common.web.AbstractGlobalExceptionHandler;
import com.agentcart.payment.exception.PaymentDeclinedException;
import com.agentcart.payment.exception.TransactionNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Translates payment-specific exceptions into the shared {@link ApiError} contract. */
@RestControllerAdvice
public class GlobalExceptionHandler extends AbstractGlobalExceptionHandler {

    @ExceptionHandler(PaymentDeclinedException.class)
    public ResponseEntity<ApiError> handleDeclined(PaymentDeclinedException ex) {
        return build(HttpStatus.PAYMENT_REQUIRED, "Payment Declined", ex.getMessage());
    }

    @ExceptionHandler(TransactionNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(TransactionNotFoundException ex) {
        return build(HttpStatus.NOT_FOUND, "Not Found", ex.getMessage());
    }
}
