package com.agentcart.inventory.dto;

import java.math.BigDecimal;

/** Current stock snapshot for a single product. */
public record StockResponse(
        String productId,
        String name,
        BigDecimal unitPrice,
        Integer availableQty,
        Integer reservedQty) {
}
