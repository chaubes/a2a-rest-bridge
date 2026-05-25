package com.agentcart.shipping.controller;

import com.agentcart.shipping.dto.CreateShipmentRequest;
import com.agentcart.shipping.dto.CreateShipmentResponse;
import com.agentcart.shipping.dto.ShipmentResponse;
import com.agentcart.shipping.service.ShippingService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** REST endpoints for creating and retrieving shipments. */
@RestController
@RequestMapping("/api/v1/shipments")
public class ShippingController {

    private final ShippingService shippingService;

    public ShippingController(ShippingService shippingService) {
        this.shippingService = shippingService;
    }

    @PostMapping
    public ResponseEntity<CreateShipmentResponse> create(@Valid @RequestBody CreateShipmentRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(shippingService.create(request));
    }

    @GetMapping("/{trackingId}")
    public ShipmentResponse getShipment(@PathVariable String trackingId) {
        return shippingService.getShipment(trackingId);
    }
}
