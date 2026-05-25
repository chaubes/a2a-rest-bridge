package com.agentcart.payment.service;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.payment.domain.Transaction;
import com.agentcart.payment.dto.ChargeRequest;
import com.agentcart.payment.dto.ChargeResponse;
import com.agentcart.payment.dto.RefundRequest;
import com.agentcart.payment.dto.RefundResponse;
import com.agentcart.payment.dto.TransactionResponse;
import com.agentcart.payment.exception.PaymentDeclinedException;
import com.agentcart.payment.exception.TransactionNotFoundException;
import com.agentcart.payment.repository.TransactionRepository;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Mock payment processing. Charges succeed unless they trip a deterministic decline
 * rule (a known test customer or an amount over the demo ceiling), making the behaviour
 * predictable for downstream callers and tests.
 */
@Service
public class PaymentService {

    private static final String SERVICE_NAME = "payment-service";
    private static final String DECLINE_CUSTOMER = "DECLINE-TEST";
    private static final BigDecimal AMOUNT_CEILING = new BigDecimal("10000");

    private final TransactionRepository repository;
    private final AuditLogger auditLogger;

    public PaymentService(TransactionRepository repository, AuditLogger auditLogger) {
        this.repository = repository;
        this.auditLogger = auditLogger;
    }

    @Transactional
    public ChargeResponse charge(ChargeRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        if (DECLINE_CUSTOMER.equals(request.customerId())) {
            throw new PaymentDeclinedException("Payment declined for customer " + request.customerId());
        }
        if (request.amount().compareTo(AMOUNT_CEILING) > 0) {
            throw new PaymentDeclinedException("Payment declined: amount exceeds the permitted ceiling");
        }

        String transactionId = "txn-" + UUID.randomUUID().toString().substring(0, 8);
        Transaction transaction = new Transaction(
                transactionId, request.customerId(), request.amount(), request.currency(),
                "SUCCESS", Instant.now());
        Transaction saved = repository.save(transaction);

        ChargeResponse response = new ChargeResponse(
                saved.getTransactionId(), saved.getStatus(), saved.getAmount(),
                saved.getCurrency(), saved.getTimestamp());
        auditLogger.log(SERVICE_NAME, "payment.charge", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional
    public RefundResponse refund(RefundRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        Transaction transaction = repository.findById(request.transactionId())
                .orElseThrow(() -> new TransactionNotFoundException(request.transactionId()));
        transaction.setStatus("REFUNDED");
        Transaction saved = repository.save(transaction);

        RefundResponse response = new RefundResponse(saved.getTransactionId(), saved.getStatus());
        auditLogger.log(SERVICE_NAME, "payment.refund", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional(readOnly = true)
    public TransactionResponse getTransaction(String transactionId) {
        Transaction transaction = repository.findById(transactionId)
                .orElseThrow(() -> new TransactionNotFoundException(transactionId));
        return new TransactionResponse(
                transaction.getTransactionId(), transaction.getCustomerId(), transaction.getAmount(),
                transaction.getCurrency(), transaction.getStatus());
    }
}
