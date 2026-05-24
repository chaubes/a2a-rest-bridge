package com.agentcart.payment.controller;

import com.agentcart.payment.dto.ChargeRequest;
import com.agentcart.payment.dto.ChargeResponse;
import com.agentcart.payment.dto.RefundRequest;
import com.agentcart.payment.dto.RefundResponse;
import com.agentcart.payment.dto.TransactionResponse;
import com.agentcart.payment.service.PaymentService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** REST endpoints for charging, refunding, and looking up payment transactions. */
@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @PostMapping("/charge")
    public ResponseEntity<ChargeResponse> charge(@Valid @RequestBody ChargeRequest request) {
        return ResponseEntity.ok(paymentService.charge(request));
    }

    @PostMapping("/refund")
    public ResponseEntity<RefundResponse> refund(@Valid @RequestBody RefundRequest request) {
        return ResponseEntity.ok(paymentService.refund(request));
    }

    @GetMapping("/transactions/{id}")
    public TransactionResponse getTransaction(@PathVariable String id) {
        return paymentService.getTransaction(id);
    }
}
