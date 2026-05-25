package com.agentcart.order.repository;

import com.agentcart.order.domain.Order;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OrderRepository extends JpaRepository<Order, String> {

    java.util.List<Order> findTop50ByOrderByCreatedAtDesc();
}
