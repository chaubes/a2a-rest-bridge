package com.agentcart.shipping.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.time.LocalDate;

/** A shipment created for an order, with a generated tracking identifier. */
@Entity
@Table(name = "shipments")
public class Shipment {

    @Id
    @Column(name = "tracking_id")
    private String trackingId;

    @Column(name = "order_id", nullable = false)
    private String orderId;

    @Column(name = "address_line1", nullable = false)
    private String addressLine1;

    @Column(name = "city", nullable = false)
    private String city;

    @Column(name = "state", nullable = false)
    private String state;

    @Column(name = "postcode", nullable = false)
    private String postcode;

    @Column(name = "country", nullable = false)
    private String country;

    @Column(name = "shipping_method", nullable = false)
    private String shippingMethod;

    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "estimated_delivery", nullable = false)
    private LocalDate estimatedDelivery;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected Shipment() {
    }

    public Shipment(String trackingId, String orderId, String addressLine1, String city, String state,
                    String postcode, String country, String shippingMethod, String status,
                    LocalDate estimatedDelivery, Instant createdAt) {
        this.trackingId = trackingId;
        this.orderId = orderId;
        this.addressLine1 = addressLine1;
        this.city = city;
        this.state = state;
        this.postcode = postcode;
        this.country = country;
        this.shippingMethod = shippingMethod;
        this.status = status;
        this.estimatedDelivery = estimatedDelivery;
        this.createdAt = createdAt;
    }

    public String getTrackingId() {
        return trackingId;
    }

    public String getOrderId() {
        return orderId;
    }

    public String getAddressLine1() {
        return addressLine1;
    }

    public String getCity() {
        return city;
    }

    public String getState() {
        return state;
    }

    public String getPostcode() {
        return postcode;
    }

    public String getCountry() {
        return country;
    }

    public String getShippingMethod() {
        return shippingMethod;
    }

    public String getStatus() {
        return status;
    }

    public LocalDate getEstimatedDelivery() {
        return estimatedDelivery;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
