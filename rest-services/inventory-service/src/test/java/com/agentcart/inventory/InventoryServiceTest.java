package com.agentcart.inventory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.inventory.domain.Product;
import com.agentcart.inventory.dto.ReserveRequest;
import com.agentcart.inventory.dto.ReserveResponse;
import com.agentcart.inventory.exception.InsufficientStockException;
import com.agentcart.inventory.exception.ProductNotFoundException;
import com.agentcart.inventory.repository.ProductRepository;
import com.agentcart.inventory.service.InventoryService;
import java.math.BigDecimal;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class InventoryServiceTest {

    private ProductRepository repository;
    private AuditLogger auditLogger;
    private InventoryService service;

    @BeforeEach
    void setUp() {
        repository = Mockito.mock(ProductRepository.class);
        auditLogger = Mockito.mock(AuditLogger.class);
        service = new InventoryService(repository, auditLogger);
    }

    @Test
    void reserveDecrementsAvailableAndIncrementsReserved() {
        Product product = new Product("WB-001", "Blue Widget", new BigDecimal("14.99"), 100, 0);
        when(repository.findById("WB-001")).thenReturn(Optional.of(product));
        when(repository.save(any(Product.class))).thenAnswer(inv -> inv.getArgument(0));

        ReserveResponse response = service.reserve(new ReserveRequest("WB-001", 10, "corr-1"));

        assertThat(response.status()).isEqualTo("RESERVED");
        assertThat(response.reservedQty()).isEqualTo(10);
        assertThat(response.remainingQty()).isEqualTo(90);
        assertThat(product.getAvailableQty()).isEqualTo(90);
        assertThat(product.getReservedQty()).isEqualTo(10);
        verify(auditLogger).log(any(), any(), any(), any(), any(), Mockito.anyLong());
    }

    @Test
    void reserveThrowsWhenStockInsufficient() {
        Product product = new Product("WB-002", "Red Widget", new BigDecimal("12.99"), 5, 0);
        when(repository.findById("WB-002")).thenReturn(Optional.of(product));

        assertThatThrownBy(() -> service.reserve(new ReserveRequest("WB-002", 10, "corr-2")))
                .isInstanceOf(InsufficientStockException.class);

        verify(repository, never()).save(any());
    }

    @Test
    void reserveThrowsWhenProductMissing() {
        when(repository.findById("ZZ-999")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.reserve(new ReserveRequest("ZZ-999", 1, "corr-3")))
                .isInstanceOf(ProductNotFoundException.class);
    }
}
