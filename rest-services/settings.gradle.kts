plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.10.0"
}

rootProject.name = "agentcart-rest-services"

include(
    "common",
    "inventory-service",
    "payment-service",
    "order-service",
    "shipping-service",
    "notification-service",
)
