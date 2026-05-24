package com.agentcart.shipping.repository;

import com.agentcart.shipping.domain.Shipment;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ShipmentRepository extends JpaRepository<Shipment, String> {
}
