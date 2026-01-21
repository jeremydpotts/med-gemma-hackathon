"""
HIPAA-compliant Audit Logging module.

Provides comprehensive audit logging for all PHI access and system events.

HIPAA requires audit logs to include:
- Who accessed the data (user ID)
- What was accessed (resource)
- When (timestamp)
- From where (IP address, location)
- What action was taken
- Result (success/failure)

Logs must be retained for minimum 6 years.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class AuditEventType(Enum):
    """Types of audit events."""
    # Data Access
    PHI_ACCESS = auto()
    PHI_MODIFY = auto()
    PHI_DELETE = auto()
    PHI_EXPORT = auto()

    # Authentication
    LOGIN_SUCCESS = auto()
    LOGIN_FAILURE = auto()
    LOGOUT = auto()
    SESSION_TIMEOUT = auto()

    # AI Operations
    INFERENCE_RUN = auto()
    REPORT_GENERATED = auto()
    REPORT_SIGNED = auto()

    # Administrative
    USER_CREATED = auto()
    USER_MODIFIED = auto()
    USER_DELETED = auto()
    PERMISSION_CHANGED = auto()
    CONFIG_CHANGED = auto()

    # Security
    ACCESS_DENIED = auto()
    SUSPICIOUS_ACTIVITY = auto()
    BREACH_DETECTED = auto()


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Represents a single audit event.

    Contains all HIPAA-required fields plus additional context.
    """
    # Required HIPAA fields
    event_id: str
    timestamp: datetime
    user_id: str
    action: AuditEventType
    resource_id: str
    result: str  # success, failure, denied

    # Additional context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: AuditSeverity = AuditSeverity.INFO

    # Integrity
    checksum: Optional[str] = None

    def __post_init__(self):
        """Calculate checksum after initialization."""
        if self.checksum is None:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum for tamper detection."""
        data = f"{self.event_id}:{self.timestamp.isoformat()}:{self.user_id}:{self.action.name}:{self.resource_id}:{self.result}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action.name,
            "resource_id": self.resource_id,
            "result": self.result,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "details": self.details,
            "severity": self.severity.value,
            "checksum": self.checksum
        }

    def verify_integrity(self) -> bool:
        """Verify event hasn't been tampered with."""
        return self.checksum == self._calculate_checksum()


# =============================================================================
# Audit Logger
# =============================================================================

class HIPAAAuditLogger:
    """
    HIPAA-compliant audit logger.

    Logs all PHI access and system events with required metadata.
    Supports multiple output destinations (file, database, remote).

    Example:
        logger = HIPAAAuditLogger()

        # Log PHI access
        logger.log_phi_access(
            user_id="dr_smith",
            resource_id="patient_12345",
            action="view",
            result="success"
        )

        # Query logs
        logs = logger.query_logs(user_id="dr_smith", days=7)
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        retention_days: int = 2192  # 6 years = ~2192 days
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for log files (default: ./audit_logs)
            retention_days: How long to retain logs (HIPAA minimum: 6 years)
        """
        self.log_dir = log_dir or Path("audit_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        # In-memory cache for recent events
        self._events: List[AuditEvent] = []
        self._max_cache_size = 10000

    def log_access(
        self,
        user_id: str,
        resource_id: str,
        action: str,
        result: str,
        **kwargs
    ) -> AuditEvent:
        """
        Log a generic access event.

        Args:
            user_id: User performing action
            resource_id: Resource being accessed
            action: Action being performed
            result: Result (success/failure/denied)
            **kwargs: Additional context (ip_address, details, etc.)

        Returns:
            Created AuditEvent
        """
        # Map string action to enum
        action_map = {
            "view": AuditEventType.PHI_ACCESS,
            "read": AuditEventType.PHI_ACCESS,
            "modify": AuditEventType.PHI_MODIFY,
            "update": AuditEventType.PHI_MODIFY,
            "delete": AuditEventType.PHI_DELETE,
            "export": AuditEventType.PHI_EXPORT,
            "inference": AuditEventType.INFERENCE_RUN,
            "login": AuditEventType.LOGIN_SUCCESS if result == "success" else AuditEventType.LOGIN_FAILURE
        }

        event_type = action_map.get(action.lower(), AuditEventType.PHI_ACCESS)

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=event_type,
            resource_id=resource_id,
            result=result,
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            session_id=kwargs.get("session_id"),
            details=kwargs.get("details", {}),
            severity=AuditSeverity.WARNING if result != "success" else AuditSeverity.INFO
        )

        self._store_event(event)
        return event

    def log_phi_access(
        self,
        user_id: str,
        resource_id: str,
        action: str = "view",
        result: str = "success",
        **kwargs
    ) -> AuditEvent:
        """
        Log PHI access event.

        Convenience method for logging PHI access with appropriate event type.

        Args:
            user_id: User accessing PHI
            resource_id: Patient/record identifier
            action: Type of access (view, modify, delete, export)
            result: Result of access attempt
            **kwargs: Additional context

        Returns:
            Created AuditEvent
        """
        return self.log_access(user_id, resource_id, action, result, **kwargs)

    def log_authentication(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> AuditEvent:
        """
        Log authentication event.

        Args:
            user_id: User attempting authentication
            success: Whether authentication succeeded
            ip_address: Source IP address
            failure_reason: Reason for failure (if applicable)

        Returns:
            Created AuditEvent
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            resource_id="authentication",
            result="success" if success else "failure",
            ip_address=ip_address,
            details={"failure_reason": failure_reason} if failure_reason else {},
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING
        )

        self._store_event(event)
        return event

    def log_inference(
        self,
        user_id: str,
        image_id: str,
        model_version: str,
        processing_time_ms: float,
        result: str = "success"
    ) -> AuditEvent:
        """
        Log AI inference event.

        Args:
            user_id: User running inference
            image_id: Image/study identifier
            model_version: Version of AI model used
            processing_time_ms: Processing time
            result: Result status

        Returns:
            Created AuditEvent
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=AuditEventType.INFERENCE_RUN,
            resource_id=image_id,
            result=result,
            details={
                "model_version": model_version,
                "processing_time_ms": processing_time_ms
            }
        )

        self._store_event(event)
        return event

    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_id: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.WARNING
    ) -> AuditEvent:
        """
        Log security-related event.

        Args:
            event_type: Type of security event
            user_id: User involved
            resource_id: Resource involved
            details: Event details
            severity: Event severity

        Returns:
            Created AuditEvent
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=event_type,
            resource_id=resource_id,
            result="alert",
            details=details,
            severity=severity
        )

        self._store_event(event)

        # Also log to Python logger for immediate visibility
        log_method = getattr(logger, severity.value, logger.warning)
        log_method(f"Security event: {event_type.name} - User: {user_id} - {details}")

        return event

    def _store_event(self, event: AuditEvent) -> None:
        """
        Store event to log file and memory cache.

        Args:
            event: Event to store
        """
        # Add to memory cache
        self._events.append(event)

        # Trim cache if needed
        if len(self._events) > self._max_cache_size:
            self._events = self._events[-self._max_cache_size:]

        # Write to file
        self._write_to_file(event)

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to daily log file."""
        date_str = event.timestamp.strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.jsonl"

        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def query_logs(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: Optional[int] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query audit logs with filters.

        Args:
            user_id: Filter by user
            resource_id: Filter by resource
            action: Filter by action type
            start_date: Start of date range
            end_date: End of date range
            days: Number of days to look back (alternative to date range)
            limit: Maximum results to return

        Returns:
            List of matching AuditEvents
        """
        # Calculate date range
        if days:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

        results = []

        # Search memory cache first
        for event in reversed(self._events):
            if self._event_matches(event, user_id, resource_id, action, start_date, end_date):
                results.append(event)
                if len(results) >= limit:
                    break

        # If not enough results, search files
        if len(results) < limit:
            file_results = self._search_files(
                user_id, resource_id, action, start_date, end_date, limit - len(results)
            )
            results.extend(file_results)

        return results[:limit]

    def _event_matches(
        self,
        event: AuditEvent,
        user_id: Optional[str],
        resource_id: Optional[str],
        action: Optional[AuditEventType],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> bool:
        """Check if event matches filter criteria."""
        if user_id and event.user_id != user_id:
            return False
        if resource_id and event.resource_id != resource_id:
            return False
        if action and event.action != action:
            return False
        if start_date and event.timestamp < start_date:
            return False
        if end_date and event.timestamp > end_date:
            return False
        return True

    def _search_files(
        self,
        user_id: Optional[str],
        resource_id: Optional[str],
        action: Optional[AuditEventType],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int
    ) -> List[AuditEvent]:
        """Search log files for matching events."""
        results = []

        # Get relevant log files
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)

        for log_file in log_files:
            try:
                with open(log_file) as f:
                    for line in f:
                        data = json.loads(line)
                        event = self._dict_to_event(data)

                        if self._event_matches(event, user_id, resource_id, action, start_date, end_date):
                            results.append(event)
                            if len(results) >= limit:
                                return results

            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")

        return results

    def _dict_to_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Convert dictionary back to AuditEvent."""
        return AuditEvent(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data["user_id"],
            action=AuditEventType[data["action"]],
            resource_id=data["resource_id"],
            result=data["result"],
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
            details=data.get("details", {}),
            severity=AuditSeverity(data.get("severity", "info")),
            checksum=data.get("checksum")
        )

    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Get all logs from memory cache.

        Returns:
            List of log dictionaries
        """
        return [event.to_dict() for event in self._events]

    def verify_log_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of audit logs.

        Returns:
            Report of integrity check results
        """
        total = 0
        verified = 0
        failed = 0

        for event in self._events:
            total += 1
            if event.verify_integrity():
                verified += 1
            else:
                failed += 1
                logger.warning(f"Integrity check failed for event {event.event_id}")

        return {
            "total_events": total,
            "verified": verified,
            "failed": failed,
            "integrity_percentage": (verified / total * 100) if total > 0 else 100
        }
