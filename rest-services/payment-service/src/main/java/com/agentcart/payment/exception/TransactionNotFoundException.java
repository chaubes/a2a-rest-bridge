package com.agentcart.payment.exception;

/** Raised when a referenced transaction cannot be found. */
public class TransactionNotFoundException extends RuntimeException {

    public TransactionNotFoundException(String transactionId) {
        super("Transaction not found: " + transactionId);
    }
}
