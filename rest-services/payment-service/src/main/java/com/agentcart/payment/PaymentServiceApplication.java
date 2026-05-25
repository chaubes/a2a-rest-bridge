package com.agentcart.payment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the payment REST service. Component scanning is widened to the
 * platform root package so the shared {@code common} infrastructure is picked up.
 */
@SpringBootApplication(scanBasePackages = "com.agentcart")
public class PaymentServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(PaymentServiceApplication.class, args);
    }
}
