package com.agentcart.inventory.service;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.common.correlation.CorrelationContext;
import com.agentcart.inventory.domain.Product;
import com.agentcart.inventory.dto.ReleaseRequest;
import com.agentcart.inventory.dto.ReleaseResponse;
import com.agentcart.inventory.dto.ReserveRequest;
import com.agentcart.inventory.dto.ReserveResponse;
import com.agentcart.inventory.dto.StockResponse;
import com.agentcart.inventory.exception.InsufficientStockException;
import com.agentcart.inventory.exception.ProductNotFoundException;
import com.agentcart.inventory.repository.ProductRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Core inventory operations: querying stock and reserving/releasing quantities.
 * Mutating operations run inside a transaction and emit an audit record.
 */
@Service
public class InventoryService {

    private static final String SERVICE_NAME = "inventory-service";

    private final ProductRepository repository;
    private final AuditLogger auditLogger;

    public InventoryService(ProductRepository repository, AuditLogger auditLogger) {
        this.repository = repository;
        this.auditLogger = auditLogger;
    }

    @Transactional(readOnly = true)
    public StockResponse getStock(String productId) {
        Product product = repository.findById(productId)
                .orElseThrow(() -> new ProductNotFoundException(productId));
        return toStockResponse(product);
    }

    @Transactional(readOnly = true)
    public List<StockResponse> listProducts() {
        return repository.findAll().stream().map(this::toStockResponse).toList();
    }

    @Transactional
    public ReserveResponse reserve(ReserveRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        Product product = repository.findById(request.productId())
                .orElseThrow(() -> new ProductNotFoundException(request.productId()));

        if (product.getAvailableQty() < request.quantity()) {
            throw new InsufficientStockException(request.productId(), request.quantity(), product.getAvailableQty());
        }

        product.setAvailableQty(product.getAvailableQty() - request.quantity());
        product.setReservedQty(product.getReservedQty() + request.quantity());
        Product saved = repository.save(product);

        ReserveResponse response = new ReserveResponse(
                saved.getProductId(), saved.getReservedQty(), saved.getAvailableQty(), "RESERVED");
        auditLogger.log(SERVICE_NAME, "stock.reserve", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    @Transactional
    public ReleaseResponse release(ReleaseRequest request) {
        long start = System.currentTimeMillis();
        String correlationId = CorrelationContext.resolve(request.correlationId());

        Product product = repository.findById(request.productId())
                .orElseThrow(() -> new ProductNotFoundException(request.productId()));

        product.setAvailableQty(product.getAvailableQty() + request.quantity());
        product.setReservedQty(Math.max(0, product.getReservedQty() - request.quantity()));
        Product saved = repository.save(product);

        ReleaseResponse response = new ReleaseResponse(saved.getProductId(), saved.getAvailableQty(), "RELEASED");
        auditLogger.log(SERVICE_NAME, "stock.release", correlationId, request, response,
                System.currentTimeMillis() - start);
        return response;
    }

    private StockResponse toStockResponse(Product product) {
        return new StockResponse(
                product.getProductId(),
                product.getName(),
                product.getUnitPrice(),
                product.getAvailableQty(),
                product.getReservedQty());
    }
}
