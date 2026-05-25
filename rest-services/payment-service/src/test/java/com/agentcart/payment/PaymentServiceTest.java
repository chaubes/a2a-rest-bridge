package com.agentcart.payment;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.payment.domain.Transaction;
import com.agentcart.payment.dto.ChargeRequest;
import com.agentcart.payment.dto.ChargeResponse;
import com.agentcart.payment.exception.PaymentDeclinedException;
import com.agentcart.payment.repository.TransactionRepository;
import com.agentcart.payment.service.PaymentService;
import java.math.BigDecimal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class PaymentServiceTest {

    private TransactionRepository repository;
    private AuditLogger auditLogger;
    private PaymentService service;

    @BeforeEach
    void setUp() {
        repository = Mockito.mock(TransactionRepository.class);
        auditLogger = Mockito.mock(AuditLogger.class);
        service = new PaymentService(repository, auditLogger);
    }

    @Test
    void chargeSavesSuccessfulTransaction() {
        when(repository.save(any(Transaction.class))).thenAnswer(inv -> inv.getArgument(0));

        ChargeResponse response = service.charge(
                new ChargeRequest("cust-1", new BigDecimal("49.99"), "AUD", "tok_visa", "corr-1"));

        assertThat(response.status()).isEqualTo("SUCCESS");
        assertThat(response.transactionId()).startsWith("txn-");
        verify(auditLogger).log(any(), any(), any(), any(), any(), Mockito.anyLong());
    }

    @Test
    void chargeIsDeclinedForKnownTestCustomer() {
        assertThatThrownBy(() -> service.charge(
                new ChargeRequest("DECLINE-TEST", new BigDecimal("49.99"), "AUD", "tok_visa", "corr-1")))
                .isInstanceOf(PaymentDeclinedException.class);

        verify(repository, never()).save(any());
    }

    @Test
    void chargeIsDeclinedAboveCeiling() {
        assertThatThrownBy(() -> service.charge(
                new ChargeRequest("cust-1", new BigDecimal("10000.01"), "AUD", "tok_visa", "corr-1")))
                .isInstanceOf(PaymentDeclinedException.class);

        verify(repository, never()).save(any());
    }
}
