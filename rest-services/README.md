# AgentCart — REST Services

The deterministic REST layer of the AgentCart demo. These Spring Boot microservices
own all persistent state, ACID transactions, input validation, and audit logging.
They are deliberately self-contained: a browser, a `curl` command, or any other HTTP
client can call the same validated endpoints, and each service embeds its own H2
in-memory database so the whole layer runs with no external infrastructure.

## Modules

| Module                 | Port | Responsibility                                            |
|------------------------|------|-----------------------------------------------------------|
| `common`               | —    | Shared library: correlation filter, audit logger, error contract, OpenAPI config |
| `order-service`        | 8080 | Create and retrieve orders                                |
| `inventory-service`    | 8081 | Stock levels; reserve/release inventory (seeded products) |
| `payment-service`      | 8082 | Mock charges, refunds, transaction lookup                 |
| `shipping-service`     | 8083 | Mock shipment creation with generated tracking IDs        |
| `notification-service` | 8084 | Mock notification dispatch with a persistent log          |

## Tech stack

- Java 21, Spring Boot 3.3.5
- Gradle (Kotlin DSL) multi-module build with a version catalog
- Spring Data JPA + Hibernate over H2 (in-memory, embedded)
- Jakarta Bean Validation
- springdoc-openapi (Swagger UI) + Spring Boot Actuator
- JUnit 5 + MockMvc for tests

## Toolchain

The build pins a Java 21 toolchain via Gradle's
`org.gradle.toolchains.foojay-resolver-convention` plugin, so Gradle will
auto-provision a JDK 21 even when a different JDK is on the host. The Gradle wrapper
(8.10) is committed, so no local Gradle install is required.

## Build and test

From this directory:

```bash
./gradlew build
```

This compiles every module and runs all tests against H2.

Build a single service's bootable jar:

```bash
./gradlew :inventory-service:bootJar
```

Run a service directly:

```bash
./gradlew :inventory-service:bootRun
```

## Per-service endpoints

All bodies and responses use camelCase JSON. Every mutating endpoint accepts a
`correlationId` in its body; an `X-Correlation-ID` request header is also honoured and
is always echoed on the response.

### inventory-service (8081)
- `GET  /api/v1/stock/{productId}`
- `GET  /api/v1/products`
- `POST /api/v1/stock/reserve` — `{productId, quantity, correlationId}`
- `POST /api/v1/stock/release` — `{productId, quantity, correlationId}`

### payment-service (8082)
- `POST /api/v1/payments/charge` — `{customerId, amount, currency, paymentMethodToken, correlationId}`
- `POST /api/v1/payments/refund` — `{transactionId, correlationId}`
- `GET  /api/v1/payments/transactions/{id}`

### order-service (8080)
- `POST /api/v1/orders` — `{customerId, productId, quantity, totalAmount, currency, transactionId, trackingId, correlationId}`
- `GET  /api/v1/orders/{id}`
- `GET  /api/v1/orders`

### shipping-service (8083)
- `POST /api/v1/shipments` — `{orderId, addressLine1, city, state, postcode, country, shippingMethod, correlationId}`
- `GET  /api/v1/shipments/{trackingId}`

### notification-service (8084)
- `POST /api/v1/notifications` — `{customerId, message, channel, correlationId}`
- `GET  /api/v1/notifications/log`

## Operational endpoints (every service)

- Health: `GET /actuator/health`
- OpenAPI JSON: `GET /v3/api-docs`
- Swagger UI: `GET /swagger-ui.html`
- H2 console: `GET /h2-console`

## Error contract

All services return the same error shape:

```json
{
  "timestamp": "2026-05-24T00:00:00Z",
  "status": 422,
  "error": "Validation Failed",
  "message": "quantity must be greater than 0",
  "path": "/api/v1/stock/reserve",
  "correlationId": "gen-1a2b3c4d"
}
```

Validation failures return HTTP 422. Business errors use their natural status:
insufficient stock → 409, declined payment → 402, missing resources → 404.

## Docker

Each service ships a multi-stage `Dockerfile`. The build context is this directory
(so the build stage can resolve the multi-module project). Example:

```bash
docker build -f inventory-service/Dockerfile -t agentcart-inventory .
```

The runtime image includes `curl` so an orchestrator health check such as
`curl -f http://localhost:8081/actuator/health` works out of the box.

## Seed data

`inventory-service` is seeded with five products: `WB-001`, `WB-002`, `WR-001`,
`WH-001`, `WS-001`, each starting with `reservedQty = 0`.

## License

Released under the MIT License.
