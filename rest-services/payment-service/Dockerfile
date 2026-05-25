# syntax=docker/dockerfile:1

# ---- Stage 1: build the bootable jar ----
FROM gradle:8.10-jdk21 AS build
WORKDIR /workspace
COPY . .
RUN gradle :payment-service:bootJar -x test --no-daemon

# ---- Stage 2: minimal runtime image ----
FROM eclipse-temurin:21-jre
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /workspace/payment-service/build/libs/*.jar app.jar
EXPOSE 8082
ENTRYPOINT ["java", "-jar", "app.jar"]
