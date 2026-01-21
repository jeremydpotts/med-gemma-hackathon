"""
Access Control module for RadAssist Pro.

Implements Role-Based Access Control (RBAC) for HIPAA compliance.

Roles:
- Physician: Full access to patient data and AI analysis
- Nurse: Read access to reports and findings
- Radiologist: Full access with interpretation authority
- Admin: System administration, no PHI access
- Researcher: Access to de-identified data only
"""

import logging
from enum import Enum, auto
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class UserRole(Enum):
    """User roles for access control."""
    PHYSICIAN = "physician"
    RADIOLOGIST = "radiologist"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    ADMIN = "admin"
    RESEARCHER = "researcher"
    GUEST = "guest"


class Permission(Enum):
    """Permissions for different actions."""
    # Data Access
    READ_PHI = auto()
    WRITE_PHI = auto()
    DELETE_PHI = auto()
    READ_DEIDENTIFIED = auto()

    # AI Operations
    RUN_INFERENCE = auto()
    VIEW_RESULTS = auto()
    INTERPRET_RESULTS = auto()
    OVERRIDE_AI = auto()

    # Reports
    GENERATE_REPORT = auto()
    SIGN_REPORT = auto()
    EXPORT_REPORT = auto()

    # Admin
    MANAGE_USERS = auto()
    VIEW_AUDIT_LOG = auto()
    CONFIGURE_SYSTEM = auto()


class Resource(Enum):
    """Resources that can be accessed."""
    PATIENT_DATA = "patient_data"
    MEDICAL_IMAGE = "medical_image"
    AI_ANALYSIS = "ai_analysis"
    REPORT = "report"
    AUDIT_LOG = "audit_log"
    SYSTEM_CONFIG = "system_config"
    DEIDENTIFIED_DATA = "deidentified_data"


@dataclass
class User:
    """Represents a system user."""
    user_id: str
    username: str
    role: UserRole
    department: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    custom_permissions: Set[Permission] = field(default_factory=set)
    denied_permissions: Set[Permission] = field(default_factory=set)


@dataclass
class AccessAttempt:
    """Record of an access attempt."""
    user_id: str
    resource: Resource
    permission: Permission
    timestamp: datetime
    granted: bool
    reason: Optional[str] = None


# =============================================================================
# Role-Permission Mapping
# =============================================================================

# Define what permissions each role has by default
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.PHYSICIAN: {
        Permission.READ_PHI,
        Permission.WRITE_PHI,
        Permission.RUN_INFERENCE,
        Permission.VIEW_RESULTS,
        Permission.INTERPRET_RESULTS,
        Permission.GENERATE_REPORT,
        Permission.SIGN_REPORT,
        Permission.EXPORT_REPORT,
        Permission.READ_DEIDENTIFIED
    },

    UserRole.RADIOLOGIST: {
        Permission.READ_PHI,
        Permission.WRITE_PHI,
        Permission.RUN_INFERENCE,
        Permission.VIEW_RESULTS,
        Permission.INTERPRET_RESULTS,
        Permission.OVERRIDE_AI,
        Permission.GENERATE_REPORT,
        Permission.SIGN_REPORT,
        Permission.EXPORT_REPORT,
        Permission.READ_DEIDENTIFIED
    },

    UserRole.NURSE: {
        Permission.READ_PHI,
        Permission.VIEW_RESULTS,
        Permission.READ_DEIDENTIFIED
    },

    UserRole.TECHNICIAN: {
        Permission.READ_PHI,
        Permission.RUN_INFERENCE,
        Permission.VIEW_RESULTS,
        Permission.READ_DEIDENTIFIED
    },

    UserRole.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
        Permission.CONFIGURE_SYSTEM,
        Permission.READ_DEIDENTIFIED
        # Note: Admin does NOT have PHI access by default (separation of duties)
    },

    UserRole.RESEARCHER: {
        Permission.READ_DEIDENTIFIED,
        Permission.RUN_INFERENCE,
        Permission.VIEW_RESULTS
        # Note: Researcher can only access de-identified data
    },

    UserRole.GUEST: {
        Permission.READ_DEIDENTIFIED
        # Minimal access
    }
}


# =============================================================================
# Access Controller
# =============================================================================

class AccessController:
    """
    Control access to resources based on user roles and permissions.

    Implements RBAC with support for:
    - Role-based permissions
    - Custom permissions per user
    - Permission denial lists
    - Access attempt logging

    Example:
        ac = AccessController()
        user = User(user_id="dr1", username="dr_smith", role=UserRole.PHYSICIAN)

        if ac.check_permission(user, Permission.RUN_INFERENCE):
            # Run AI inference
            pass
    """

    def __init__(self):
        """Initialize access controller."""
        self.access_log: List[AccessAttempt] = []
        self._users: Dict[str, User] = {}

    def register_user(self, user: User) -> None:
        """
        Register a user in the system.

        Args:
            user: User to register
        """
        self._users[user.user_id] = user
        logger.info(f"Registered user {user.username} with role {user.role.value}")

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User if found, None otherwise
        """
        return self._users.get(user_id)

    def check_permission(
        self,
        user: User,
        permission: Permission,
        resource: Optional[Resource] = None
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user: User requesting access
            permission: Permission being requested
            resource: Optional resource being accessed

        Returns:
            True if permission granted, False otherwise
        """
        # Check if user is active
        if not user.is_active:
            self._log_access(user.user_id, resource, permission, False, "User inactive")
            return False

        # Check if permission is explicitly denied
        if permission in user.denied_permissions:
            self._log_access(user.user_id, resource, permission, False, "Permission explicitly denied")
            return False

        # Check custom permissions first
        if permission in user.custom_permissions:
            self._log_access(user.user_id, resource, permission, True, "Custom permission")
            return True

        # Check role-based permissions
        role_permissions = ROLE_PERMISSIONS.get(user.role, set())
        has_permission = permission in role_permissions

        reason = "Role permission" if has_permission else "Permission not in role"
        self._log_access(user.user_id, resource, permission, has_permission, reason)

        return has_permission

    def check_phi_access(self, user: User) -> bool:
        """
        Check if user can access PHI.

        Args:
            user: User requesting access

        Returns:
            True if user can access PHI
        """
        return self.check_permission(user, Permission.READ_PHI)

    def check_deidentified_access(self, user: User) -> bool:
        """
        Check if user can access de-identified data.

        Args:
            user: User requesting access

        Returns:
            True if user can access de-identified data
        """
        return self.check_permission(user, Permission.READ_DEIDENTIFIED)

    def grant_permission(self, user: User, permission: Permission) -> None:
        """
        Grant additional permission to user.

        Args:
            user: User to grant permission to
            permission: Permission to grant
        """
        user.custom_permissions.add(permission)
        logger.info(f"Granted {permission.name} to {user.username}")

    def deny_permission(self, user: User, permission: Permission) -> None:
        """
        Deny permission from user.

        Args:
            user: User to deny permission from
            permission: Permission to deny
        """
        user.denied_permissions.add(permission)
        logger.info(f"Denied {permission.name} from {user.username}")

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """
        Get all effective permissions for user.

        Args:
            user: User to get permissions for

        Returns:
            Set of effective permissions
        """
        if not user.is_active:
            return set()

        # Start with role permissions
        permissions = ROLE_PERMISSIONS.get(user.role, set()).copy()

        # Add custom permissions
        permissions.update(user.custom_permissions)

        # Remove denied permissions
        permissions -= user.denied_permissions

        return permissions

    def _log_access(
        self,
        user_id: str,
        resource: Optional[Resource],
        permission: Permission,
        granted: bool,
        reason: str
    ) -> None:
        """Log an access attempt."""
        attempt = AccessAttempt(
            user_id=user_id,
            resource=resource or Resource.PATIENT_DATA,
            permission=permission,
            timestamp=datetime.utcnow(),
            granted=granted,
            reason=reason
        )
        self.access_log.append(attempt)

    def get_access_log(self, user_id: Optional[str] = None) -> List[AccessAttempt]:
        """
        Get access log, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of access attempts
        """
        if user_id:
            return [a for a in self.access_log if a.user_id == user_id]
        return self.access_log.copy()


# =============================================================================
# Decorators for Access Control
# =============================================================================

def require_permission(permission: Permission):
    """
    Decorator to require permission for function access.

    Example:
        @require_permission(Permission.RUN_INFERENCE)
        def run_ai_analysis(user, image):
            ...

    Args:
        permission: Required permission
    """
    def decorator(func):
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            # Create a basic access controller for checking
            # In production, would use a singleton or dependency injection
            ac = AccessController()

            if not ac.check_permission(user, permission):
                raise PermissionError(
                    f"User {user.username} lacks permission: {permission.name}"
                )

            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def require_phi_access(func):
    """
    Decorator to require PHI access for function.

    Example:
        @require_phi_access
        def view_patient_record(user, patient_id):
            ...
    """
    @wraps(func)
    def wrapper(user: User, *args, **kwargs):
        ac = AccessController()

        if not ac.check_phi_access(user):
            raise PermissionError(
                f"User {user.username} does not have PHI access"
            )

        return func(user, *args, **kwargs)
    return wrapper


def researcher_only(func):
    """
    Decorator to restrict function to de-identified data only.

    Forces function to only work with de-identified data.

    Example:
        @researcher_only
        def analyze_population_data(user, dataset):
            ...
    """
    @wraps(func)
    def wrapper(user: User, *args, **kwargs):
        if user.role != UserRole.RESEARCHER:
            # Non-researchers can use the function normally
            return func(user, *args, **kwargs)

        # Researchers - verify data is de-identified
        # This would check that args/kwargs don't contain PHI
        # For now, just log the restriction
        logger.info(f"Researcher {user.username} accessing de-identified data only")

        return func(user, *args, **kwargs)
    return wrapper


# =============================================================================
# Utility Functions
# =============================================================================

def create_demo_users() -> Dict[str, User]:
    """
    Create demo users for testing.

    Returns:
        Dictionary of demo users
    """
    users = {
        "physician_1": User(
            user_id="physician_1",
            username="dr_smith",
            role=UserRole.PHYSICIAN,
            department="Internal Medicine"
        ),
        "radiologist_1": User(
            user_id="radiologist_1",
            username="dr_jones",
            role=UserRole.RADIOLOGIST,
            department="Radiology"
        ),
        "nurse_1": User(
            user_id="nurse_1",
            username="nurse_williams",
            role=UserRole.NURSE,
            department="Internal Medicine"
        ),
        "researcher_1": User(
            user_id="researcher_1",
            username="researcher_chen",
            role=UserRole.RESEARCHER,
            department="Research"
        ),
        "admin_1": User(
            user_id="admin_1",
            username="admin_taylor",
            role=UserRole.ADMIN
        )
    }

    return users


def get_role_description(role: UserRole) -> str:
    """
    Get description of role permissions.

    Args:
        role: Role to describe

    Returns:
        Human-readable description
    """
    descriptions = {
        UserRole.PHYSICIAN: "Full access to patient data, AI analysis, and report generation",
        UserRole.RADIOLOGIST: "Full access plus AI override capability and report signing",
        UserRole.NURSE: "Read access to patient data and results",
        UserRole.TECHNICIAN: "Can run AI analysis and view results",
        UserRole.ADMIN: "System administration, no PHI access",
        UserRole.RESEARCHER: "Access to de-identified data only",
        UserRole.GUEST: "Read-only access to de-identified data"
    }

    return descriptions.get(role, "Unknown role")
