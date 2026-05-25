plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
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
