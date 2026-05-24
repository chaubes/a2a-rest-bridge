package com.agentcart.order.service;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.order.domain.Order;
import com.agentcart.order.dto.CreateOrderRequest;
import com.agentcart.order.dto.OrderResponse;
import com.agentcart.order.exception.OrderNotFoundException;
import com.agentcart.order.repository.OrderRepository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Creates and retrieves orders, emitting an audit record on creation. */
@Service
public class OrderService {

    private static final String SERVICE_NAME = "order-service";

    private final OrderRepository repository;
    private final AuditLogger auditLogger;

    public OrderService(OrderRepository repository, AuditLogger auditLogger) {
        this.repository = repository;
        this.auditLogger = auditLogger;
    }

    @Transactional
    public OrderResponse create(CreateOrderRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        String orderId = "ord-" + UUID.randomUUID().toString().substring(0, 8);
        Order order = new Order(
                orderId, request.customerId(), request.productId(), request.quantity(),
                request.totalAmount(), request.currency(), request.transactionId(),
                request.trackingId(), "CONFIRMED", Instant.now());
        Order saved = repository.save(order);

        OrderResponse response = toResponse(saved);
        auditLogger.log(SERVICE_NAME, "order.create", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrder(String orderId) {
        Order order = repository.findById(orderId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));
        return toResponse(order);
    }

    @Transactional(readOnly = true)
    public List<OrderResponse> recentOrders() {
        return repository.findTop50ByOrderByCreatedAtDesc().stream().map(this::toResponse).toList();
    }

    private OrderResponse toResponse(Order order) {
        return new OrderResponse(
                order.getOrderId(), order.getCustomerId(), order.getProductId(), order.getQuantity(),
                order.getTotalAmount(), order.getCurrency(), order.getTransactionId(),
                order.getTrackingId(), order.getStatus(), order.getCreatedAt());
    }
}
