"""
Security module for RadAssist Pro.

This module provides HIPAA-compliant security features including:
- PHI detection and de-identification
- Data encryption
- Access control
- Audit logging
- Breach detection

⚠️ IMPORTANT: This is a demonstration/research implementation.
For production use, conduct full security audit and compliance review.
"""

from .deidentification import (
    PHIDetector,
    DataDeidentifier,
    DICOMDeidentifier,
    HIPAA_IDENTIFIERS
)

from .encryption import (
    PHIEncryption,
    SecureStorage
)

from .access_control import (
    UserRole,
    AccessController,
    Permission
)

from .audit_log import (
    HIPAAAuditLogger,
    AuditEvent
)

from .breach_detection import (
    BreachDetector,
    SecurityAlert
)

__all__ = [
    # De-identification
    "PHIDetector",
    "DataDeidentifier",
    "DICOMDeidentifier",
    "HIPAA_IDENTIFIERS",
    # Encryption
    "PHIEncryption",
    "SecureStorage",
    # Access Control
    "UserRole",
    "AccessController",
    "Permission",
    # Audit
    "HIPAAAuditLogger",
    "AuditEvent",
    # Breach Detection
    "BreachDetector",
    "SecurityAlert"
]
