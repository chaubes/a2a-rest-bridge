package com.agentcart.inventory.controller;

import com.agentcart.inventory.dto.ReleaseRequest;
import com.agentcart.inventory.dto.ReleaseResponse;
import com.agentcart.inventory.dto.ReserveRequest;
import com.agentcart.inventory.dto.ReserveResponse;
import com.agentcart.inventory.dto.StockResponse;
import com.agentcart.inventory.service.InventoryService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** REST endpoints for stock queries and reserve/release operations. */
@RestController
@RequestMapping("/api/v1")
public class InventoryController {

    private final InventoryService inventoryService;

    public InventoryController(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    @GetMapping("/stock/{productId}")
    public StockResponse getStock(@PathVariable String productId) {
        return inventoryService.getStock(productId);
    }

    @GetMapping("/products")
    public List<StockResponse> listProducts() {
        return inventoryService.listProducts();
    }

    @PostMapping("/stock/reserve")
    public ResponseEntity<ReserveResponse> reserve(@Valid @RequestBody ReserveRequest request) {
        return ResponseEntity.ok(inventoryService.reserve(request));
    }

    @PostMapping("/stock/release")
    public ResponseEntity<ReleaseResponse> release(@Valid @RequestBody ReleaseRequest request) {
        return ResponseEntity.ok(inventoryService.release(request));
    }
}
