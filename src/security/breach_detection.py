"""
Security Breach Detection module.

Monitors for suspicious activity and potential security breaches.

Detection patterns:
- Excessive data access
- Access outside normal hours
- Unusual geographic access
- Failed authentication attempts
- Large data exports

HIPAA requires breach notification within 60 days.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class AlertSeverity(Enum):
    """Severity levels for security alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of security alerts."""
    EXCESSIVE_ACCESS = auto()
    UNUSUAL_HOURS = auto()
    GEOGRAPHIC_ANOMALY = auto()
    FAILED_AUTH = auto()
    LARGE_EXPORT = auto()
    PRIVILEGE_ESCALATION = auto()
    DATA_EXFILTRATION = auto()
    BRUTE_FORCE = auto()
    SUSPICIOUS_PATTERN = auto()


@dataclass
class SecurityAlert:
    """Represents a security alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    user_id: str
    description: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.name,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes
        }


@dataclass
class DetectionThresholds:
    """Configurable thresholds for breach detection."""
    # Access thresholds
    max_accesses_per_hour: int = 100
    max_accesses_per_day: int = 500
    max_unique_records_per_hour: int = 50

    # Authentication thresholds
    max_failed_logins: int = 5
    failed_login_window_minutes: int = 15

    # Export thresholds
    max_export_records: int = 100
    max_export_size_mb: float = 50.0

    # Time-based thresholds
    normal_hours_start: int = 6  # 6 AM
    normal_hours_end: int = 22  # 10 PM


# =============================================================================
# Breach Detector
# =============================================================================

class BreachDetector:
    """
    Detect potential security breaches and suspicious activity.

    Monitors access patterns and generates alerts when thresholds
    are exceeded or anomalies are detected.

    Example:
        detector = BreachDetector()

        # Check for excessive access
        alert = detector.check_excessive_access(
            user_id="user_123",
            access_count=150,
            time_window_hours=1
        )
        if alert:
            print(f"Alert: {alert.description}")
    """

    def __init__(self, thresholds: Optional[DetectionThresholds] = None):
        """
        Initialize breach detector.

        Args:
            thresholds: Custom detection thresholds
        """
        self.thresholds = thresholds or DetectionThresholds()
        self._alerts: List[SecurityAlert] = []
        self._alert_counter = 0

        # Track access patterns
        self._access_counts: Dict[str, List[datetime]] = defaultdict(list)
        self._failed_logins: Dict[str, List[datetime]] = defaultdict(list)
        self._accessed_records: Dict[str, Set[str]] = defaultdict(set)

    def check_unusual_access(
        self,
        user_id: str,
        access_count: int,
        time_window_hours: float
    ) -> Dict[str, Any]:
        """
        Check for unusual access patterns.

        Args:
            user_id: User to check
            access_count: Number of accesses in window
            time_window_hours: Time window in hours

        Returns:
            Dictionary with alert status and details
        """
        # Calculate threshold based on time window
        if time_window_hours <= 1:
            threshold = self.thresholds.max_accesses_per_hour
        else:
            threshold = int(self.thresholds.max_accesses_per_day * (time_window_hours / 24))

        if access_count > threshold:
            alert = self._create_alert(
                alert_type=AlertType.EXCESSIVE_ACCESS,
                severity=self._calculate_severity(access_count, threshold),
                user_id=user_id,
                description=f"Excessive data access: {access_count} accesses in {time_window_hours} hours (threshold: {threshold})",
                details={
                    "access_count": access_count,
                    "time_window_hours": time_window_hours,
                    "threshold": threshold
                }
            )
            return {"alert": True, "reason": "excessive_access", "alert_id": alert.alert_id}

        return {"alert": False}

    def check_access_pattern(
        self,
        user_id: str,
        resource_id: str,
        access_time: datetime
    ) -> Optional[SecurityAlert]:
        """
        Check if access pattern is suspicious.

        Args:
            user_id: User accessing resource
            resource_id: Resource being accessed
            access_time: Time of access

        Returns:
            SecurityAlert if suspicious, None otherwise
        """
        alerts = []

        # Record access
        self._access_counts[user_id].append(access_time)
        self._accessed_records[user_id].add(resource_id)

        # Check hourly access count
        hour_ago = access_time - timedelta(hours=1)
        recent_accesses = [t for t in self._access_counts[user_id] if t > hour_ago]

        if len(recent_accesses) > self.thresholds.max_accesses_per_hour:
            alerts.append(self._create_alert(
                AlertType.EXCESSIVE_ACCESS,
                AlertSeverity.HIGH,
                user_id,
                f"User {user_id} exceeded hourly access limit",
                {"count": len(recent_accesses)}
            ))

        # Check unique records accessed
        if len(self._accessed_records[user_id]) > self.thresholds.max_unique_records_per_hour:
            alerts.append(self._create_alert(
                AlertType.DATA_EXFILTRATION,
                AlertSeverity.HIGH,
                user_id,
                f"User {user_id} accessed unusual number of unique records",
                {"unique_records": len(self._accessed_records[user_id])}
            ))

        # Check for access outside normal hours
        if not self._is_normal_hours(access_time):
            alerts.append(self._create_alert(
                AlertType.UNUSUAL_HOURS,
                AlertSeverity.MEDIUM,
                user_id,
                f"Access outside normal hours: {access_time.hour}:00",
                {"hour": access_time.hour}
            ))

        # Return most severe alert if any
        if alerts:
            return max(alerts, key=lambda a: self._severity_rank(a.severity))
        return None

    def check_failed_authentication(
        self,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> Optional[SecurityAlert]:
        """
        Track failed authentication attempts.

        Args:
            user_id: User attempting authentication
            ip_address: Source IP address

        Returns:
            SecurityAlert if threshold exceeded
        """
        now = datetime.utcnow()
        self._failed_logins[user_id].append(now)

        # Clean old entries
        window = now - timedelta(minutes=self.thresholds.failed_login_window_minutes)
        self._failed_logins[user_id] = [
            t for t in self._failed_logins[user_id] if t > window
        ]

        if len(self._failed_logins[user_id]) >= self.thresholds.max_failed_logins:
            return self._create_alert(
                AlertType.BRUTE_FORCE,
                AlertSeverity.HIGH,
                user_id,
                f"Multiple failed login attempts for {user_id}",
                {
                    "attempts": len(self._failed_logins[user_id]),
                    "window_minutes": self.thresholds.failed_login_window_minutes,
                    "ip_address": ip_address
                }
            )

        return None

    def check_large_export(
        self,
        user_id: str,
        record_count: int,
        size_mb: float
    ) -> Optional[SecurityAlert]:
        """
        Check for suspicious large data exports.

        Args:
            user_id: User exporting data
            record_count: Number of records
            size_mb: Size in megabytes

        Returns:
            SecurityAlert if thresholds exceeded
        """
        if record_count > self.thresholds.max_export_records:
            return self._create_alert(
                AlertType.LARGE_EXPORT,
                AlertSeverity.HIGH,
                user_id,
                f"Large data export: {record_count} records",
                {"record_count": record_count, "size_mb": size_mb}
            )

        if size_mb > self.thresholds.max_export_size_mb:
            return self._create_alert(
                AlertType.LARGE_EXPORT,
                AlertSeverity.HIGH,
                user_id,
                f"Large data export: {size_mb:.1f} MB",
                {"record_count": record_count, "size_mb": size_mb}
            )

        return None

    def _is_normal_hours(self, dt: datetime) -> bool:
        """Check if time is within normal working hours."""
        return self.thresholds.normal_hours_start <= dt.hour < self.thresholds.normal_hours_end

    def _calculate_severity(self, value: int, threshold: int) -> AlertSeverity:
        """Calculate severity based on how much threshold is exceeded."""
        ratio = value / threshold

        if ratio >= 5:
            return AlertSeverity.CRITICAL
        elif ratio >= 3:
            return AlertSeverity.HIGH
        elif ratio >= 2:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _severity_rank(self, severity: AlertSeverity) -> int:
        """Get numeric rank for severity (for sorting)."""
        ranks = {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4
        }
        return ranks.get(severity, 0)

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        user_id: str,
        description: str,
        details: Dict[str, Any]
    ) -> SecurityAlert:
        """Create and store a new alert."""
        self._alert_counter += 1

        alert = SecurityAlert(
            alert_id=f"ALERT_{self._alert_counter:06d}",
            alert_type=alert_type,
            severity=severity,
            user_id=user_id,
            description=description,
            timestamp=datetime.utcnow(),
            details=details
        )

        self._alerts.append(alert)

        # Log the alert
        log_level = {
            AlertSeverity.LOW: logger.info,
            AlertSeverity.MEDIUM: logger.warning,
            AlertSeverity.HIGH: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }

        log_level.get(severity, logger.warning)(
            f"Security Alert [{severity.value.upper()}]: {description}"
        )

        return alert

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None
    ) -> List[SecurityAlert]:
        """
        Get alerts with optional filters.

        Args:
            severity: Filter by severity
            acknowledged: Filter by acknowledgment status
            resolved: Filter by resolution status

        Returns:
            List of matching alerts
        """
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return alerts

    def acknowledge_alert(self, alert_id: str, notes: Optional[str] = None) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert to acknowledge
            notes: Optional acknowledgment notes

        Returns:
            True if successful
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                if notes:
                    alert.resolution_notes = notes
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False

    def resolve_alert(self, alert_id: str, notes: str) -> bool:
        """
        Mark alert as resolved.

        Args:
            alert_id: Alert to resolve
            notes: Resolution notes

        Returns:
            True if successful
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_notes = notes
                logger.info(f"Alert {alert_id} resolved: {notes}")
                return True
        return False

    def get_breach_report(self) -> Dict[str, Any]:
        """
        Generate breach detection report.

        Returns:
            Summary of alerts and activity
        """
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        alerts_24h = [a for a in self._alerts if a.timestamp > day_ago]
        alerts_7d = [a for a in self._alerts if a.timestamp > week_ago]

        return {
            "report_generated": now.isoformat(),
            "alerts_last_24h": len(alerts_24h),
            "alerts_last_7d": len(alerts_7d),
            "total_alerts": len(self._alerts),
            "unacknowledged": len([a for a in self._alerts if not a.acknowledged]),
            "unresolved": len([a for a in self._alerts if not a.resolved]),
            "by_severity": {
                "critical": len([a for a in self._alerts if a.severity == AlertSeverity.CRITICAL]),
                "high": len([a for a in self._alerts if a.severity == AlertSeverity.HIGH]),
                "medium": len([a for a in self._alerts if a.severity == AlertSeverity.MEDIUM]),
                "low": len([a for a in self._alerts if a.severity == AlertSeverity.LOW])
            },
            "by_type": {
                t.name: len([a for a in self._alerts if a.alert_type == t])
                for t in AlertType
            }
        }

    def reset_user_tracking(self, user_id: str) -> None:
        """
        Reset tracking data for a user.

        Use after investigating an alert to reset counters.

        Args:
            user_id: User to reset
        """
        self._access_counts[user_id] = []
        self._failed_logins[user_id] = []
        self._accessed_records[user_id] = set()
        logger.info(f"Reset tracking data for user {user_id}")


# =============================================================================
# Utility Functions
# =============================================================================

def create_breach_notification(alert: SecurityAlert) -> Dict[str, Any]:
    """
    Create HIPAA breach notification document.

    HIPAA requires notification within 60 days of breach discovery.

    Args:
        alert: Alert that triggered breach notification

    Returns:
        Breach notification document
    """
    return {
        "notification_type": "HIPAA Breach Notification",
        "discovery_date": alert.timestamp.isoformat(),
        "notification_deadline": (alert.timestamp + timedelta(days=60)).isoformat(),
        "alert_id": alert.alert_id,
        "alert_type": alert.alert_type.name,
        "severity": alert.severity.value,
        "description": alert.description,
        "affected_user": alert.user_id,
        "details": alert.details,
        "required_actions": [
            "Investigate the incident",
            "Determine scope of potential breach",
            "Identify affected individuals",
            "Prepare notification to affected individuals (if required)",
            "Report to HHS if >500 individuals affected",
            "Document remediation steps"
        ],
        "hipaa_reference": "45 CFR 164.400-414"
    }
