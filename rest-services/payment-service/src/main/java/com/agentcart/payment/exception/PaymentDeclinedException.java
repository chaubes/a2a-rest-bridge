package com.agentcart.payment.exception;

/** Raised when a charge is rejected by the (mock) payment processor. */
public class PaymentDeclinedException extends RuntimeException {

    public PaymentDeclinedException(String reason) {
        super(reason);
    }
}
