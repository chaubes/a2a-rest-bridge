package com.agentcart.inventory;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.agentcart.common.audit.AuditLogger;
import com.agentcart.inventory.controller.InventoryController;
import com.agentcart.inventory.dto.ReserveResponse;
import com.agentcart.inventory.exception.InsufficientStockException;
import com.agentcart.inventory.exception.ProductNotFoundException;
import com.agentcart.inventory.service.InventoryService;
import com.agentcart.inventory.web.GlobalExceptionHandler;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(InventoryController.class)
@Import(GlobalExceptionHandler.class)
class InventoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private InventoryService inventoryService;

    @MockBean
    private AuditLogger auditLogger;

    @Test
    void reserveReturnsReservedStatusOnSuccess() throws Exception {
        when(inventoryService.reserve(any()))
                .thenReturn(new ReserveResponse("WB-001", 5, 95, "RESERVED"));

        String body = objectMapper.writeValueAsString(
                new java.util.LinkedHashMap<>() {{
                    put("productId", "WB-001");
                    put("quantity", 5);
                    put("correlationId", "corr-123");
                }});

        mockMvc.perform(post("/api/v1/stock/reserve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("RESERVED"))
                .andExpect(jsonPath("$.reservedQty").value(5))
                .andExpect(jsonPath("$.remainingQty").value(95));
    }

    @Test
    void reserveWithInvalidQuantityReturns422() throws Exception {
        String body = objectMapper.writeValueAsString(
                new java.util.LinkedHashMap<>() {{
                    put("productId", "WB-001");
                    put("quantity", 0);
                    put("correlationId", "corr-123");
                }});

        mockMvc.perform(post("/api/v1/stock/reserve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status").value(422))
                .andExpect(jsonPath("$.error").value("Validation Failed"))
                .andExpect(jsonPath("$.correlationId").exists());
    }

    @Test
    void reserveWithInsufficientStockReturns409() throws Exception {
        when(inventoryService.reserve(any()))
                .thenThrow(new InsufficientStockException("WB-001", 500, 100));

        String body = objectMapper.writeValueAsString(
                new java.util.LinkedHashMap<>() {{
                    put("productId", "WB-001");
                    put("quantity", 500);
                    put("correlationId", "corr-123");
                }});

        mockMvc.perform(post("/api/v1/stock/reserve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.error").value("Insufficient Stock"));
    }

    @Test
    void getStockForMissingProductReturns404() throws Exception {
        when(inventoryService.getStock("ZZ-999"))
                .thenThrow(new ProductNotFoundException("ZZ-999"));

        mockMvc.perform(get("/api/v1/stock/ZZ-999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"));
    }
}
