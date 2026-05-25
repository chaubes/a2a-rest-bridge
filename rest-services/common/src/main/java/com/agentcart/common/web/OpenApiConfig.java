package com.agentcart.common.web;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Registers a baseline OpenAPI document for each service, titled after the running
 * application so the generated docs and Swagger UI are self-describing.
 */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI agentCartOpenAPI(@Value("${spring.application.name:agentcart-service}") String applicationName) {
        return new OpenAPI().info(new Info()
                .title(applicationName + " API")
                .description("AgentCart REST layer — " + applicationName)
                .version("1.0.0")
                .license(new License().name("MIT")));
    }
}
