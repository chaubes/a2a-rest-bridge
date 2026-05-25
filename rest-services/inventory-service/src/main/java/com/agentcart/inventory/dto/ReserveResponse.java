package com.agentcart.inventory.dto;

/** Result of a successful stock reservation. */
public record ReserveResponse(
        String productId,
        Integer reservedQty,
        Integer remainingQty,
        String status) {
}
