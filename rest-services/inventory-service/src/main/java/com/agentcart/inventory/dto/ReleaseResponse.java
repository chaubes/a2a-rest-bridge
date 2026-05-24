package com.agentcart.inventory.dto;

/** Result of a successful stock release. */
public record ReleaseResponse(
        String productId,
        Integer availableQty,
        String status) {
}
