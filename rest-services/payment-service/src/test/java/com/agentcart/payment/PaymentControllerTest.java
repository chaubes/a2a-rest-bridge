package com.agentcart.payment;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.payment.controller.PaymentController;
import com.agentcart.payment.dto.ChargeResponse;
import com.agentcart.payment.exception.PaymentDeclinedException;
import com.agentcart.payment.service.PaymentService;
import com.agentcart.payment.web.GlobalExceptionHandler;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(PaymentController.class)
@Import(GlobalExceptionHandler.class)
class PaymentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private PaymentService paymentService;

    @MockBean
    private AuditLogger auditLogger;

    private String chargeBody(String customerId, Object amount, String currency) throws Exception {
        return objectMapper.writeValueAsString(new LinkedHashMap<>() {{
            put("customerId", customerId);
            put("amount", amount);
            put("currency", currency);
            put("paymentMethodToken", "tok_visa");
            put("correlationId", "corr-123");
        }});
    }

    @Test
    void chargeSucceedsAndReturnsTransaction() throws Exception {
        when(paymentService.charge(any())).thenReturn(new ChargeResponse(
                "txn-abc12345", "SUCCESS", new BigDecimal("49.99"), "AUD", Instant.now()));

        mockMvc.perform(post("/api/v1/payments/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(chargeBody("cust-1", "49.99", "AUD")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"))
                .andExpect(jsonPath("$.transactionId").value("txn-abc12345"));
    }

    @Test
    void chargeWithBadCurrencyReturns422() throws Exception {
        mockMvc.perform(post("/api/v1/payments/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(chargeBody("cust-1", "49.99", "JPY")))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status").value(422))
                .andExpect(jsonPath("$.error").value("Validation Failed"));
    }

    @Test
    void declinedChargeReturns402() throws Exception {
        when(paymentService.charge(any()))
                .thenThrow(new PaymentDeclinedException("Payment declined for customer DECLINE-TEST"));

        mockMvc.perform(post("/api/v1/payments/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(chargeBody("DECLINE-TEST", "49.99", "AUD")))
                .andExpect(status().isPaymentRequired())
                .andExpect(jsonPath("$.status").value(402))
                .andExpect(jsonPath("$.error").value("Payment Declined"));
    }
}
