package com.agentcart.shipping.service;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.shipping.domain.Shipment;
import com.agentcart.shipping.dto.CreateShipmentRequest;
import com.agentcart.shipping.dto.CreateShipmentResponse;
import com.agentcart.shipping.dto.ShipmentResponse;
import com.agentcart.shipping.exception.ShipmentNotFoundException;
import com.agentcart.shipping.repository.ShipmentRepository;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

/**
 * Mock shipment creation. Generates a tracking id and an estimated delivery date based
 * on the chosen shipping method (express ships faster than standard).
 */
@Service
public class ShippingService {

    private static final String SERVICE_NAME = "shipping-service";
    private static final String DEFAULT_METHOD = "standard";

    private final ShipmentRepository repository;
    private final AuditLogger auditLogger;

    public ShippingService(ShipmentRepository repository, AuditLogger auditLogger) {
        this.repository = repository;
        this.auditLogger = auditLogger;
    }

    @Transactional
    public CreateShipmentResponse create(CreateShipmentRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        String method = StringUtils.hasText(request.shippingMethod())
                ? request.shippingMethod()
                : DEFAULT_METHOD;
        LocalDate estimatedDelivery = LocalDate.now().plusDays("express".equalsIgnoreCase(method) ? 1 : 3);
        String trackingId = "trk-" + UUID.randomUUID().toString().substring(0, 8);

        Shipment shipment = new Shipment(
                trackingId, request.orderId(), request.addressLine1(), request.city(), request.state(),
                request.postcode(), request.country(), method, "CREATED", estimatedDelivery, Instant.now());
        Shipment saved = repository.save(shipment);

        CreateShipmentResponse response = new CreateShipmentResponse(
                saved.getTrackingId(), saved.getOrderId(), saved.getStatus(),
                saved.getEstimatedDelivery(), saved.getShippingMethod());
        auditLogger.log(SERVICE_NAME, "shipment.create", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional(readOnly = true)
    public ShipmentResponse getShipment(String trackingId) {
        Shipment shipment = repository.findById(trackingId)
                .orElseThrow(() -> new ShipmentNotFoundException(trackingId));
        return new ShipmentResponse(
                shipment.getTrackingId(), shipment.getOrderId(), shipment.getAddressLine1(), shipment.getCity(),
                shipment.getState(), shipment.getPostcode(), shipment.getCountry(), shipment.getShippingMethod(),
                shipment.getStatus(), shipment.getEstimatedDelivery(), shipment.getCreatedAt());
    }
}
