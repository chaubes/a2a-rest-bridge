package com.agentcart.inventory.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import java.math.BigDecimal;

/**
 * A product held in inventory, tracking both available and reserved quantities.
 * The {@code version} column provides optimistic locking so concurrent
 * reserve/release operations do not silently overwrite one another.
 */
@Entity
@Table(name = "products")
public class Product {

    @Id
    @Column(name = "product_id")
    private String productId;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "unit_price", precision = 10, scale = 2, nullable = false)
    private BigDecimal unitPrice;

    @Column(name = "available_qty", nullable = false)
    private Integer availableQty;

    @Column(name = "reserved_qty", nullable = false)
    private Integer reservedQty;

    @Version
    @Column(name = "version")
    private Long version;

    protected Product() {
    }

    public Product(String productId, String name, BigDecimal unitPrice, Integer availableQty, Integer reservedQty) {
        this.productId = productId;
        this.name = name;
        this.unitPrice = unitPrice;
        this.availableQty = availableQty;
        this.reservedQty = reservedQty;
    }

    public String getProductId() {
        return productId;
    }

    public String getName() {
        return name;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }

    public Integer getAvailableQty() {
        return availableQty;
    }

    public void setAvailableQty(Integer availableQty) {
        this.availableQty = availableQty;
    }

    public Integer getReservedQty() {
        return reservedQty;
    }

    public void setReservedQty(Integer reservedQty) {
        this.reservedQty = reservedQty;
    }

    public Long getVersion() {
        return version;
    }
}
