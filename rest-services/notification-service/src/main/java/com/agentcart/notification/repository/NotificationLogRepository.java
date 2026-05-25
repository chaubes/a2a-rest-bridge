package com.agentcart.notification.repository;

import com.agentcart.notification.domain.NotificationLog;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificationLogRepository extends JpaRepository<NotificationLog, String> {

    List<NotificationLog> findTop50ByOrderBySentAtDesc();
}
