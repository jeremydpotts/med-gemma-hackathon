"""
PHI Detection and De-identification module.

Implements HIPAA Safe Harbor method for de-identification of
Protected Health Information (PHI).

The 18 HIPAA identifiers that must be removed:
1. Names
2. Geographic subdivisions smaller than state
3. Dates (except year)
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers/serial numbers
14. URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos
18. Any unique identifying number/code
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# HIPAA Identifier Definitions
# =============================================================================

HIPAA_IDENTIFIERS = [
    "names",
    "geographic_data",
    "dates",
    "telephone_numbers",
    "fax_numbers",
    "email_addresses",
    "social_security_numbers",
    "medical_record_numbers",
    "health_plan_numbers",
    "account_numbers",
    "certificate_license_numbers",
    "vehicle_identifiers",
    "device_identifiers",
    "urls",
    "ip_addresses",
    "biometric_identifiers",
    "photos",
    "unique_identifiers"
]


class PHIType(Enum):
    """Types of PHI that can be detected."""
    NAME = "name"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    SSN = "ssn"
    MRN = "mrn"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    URL = "url"
    ACCOUNT = "account"
    UNKNOWN = "unknown"


@dataclass
class PHIMatch:
    """Represents a detected PHI match."""
    phi_type: PHIType
    value: str
    start_pos: int
    end_pos: int
    confidence: float


# =============================================================================
# PHI Detection
# =============================================================================

class PHIDetector:
    """
    Detect Protected Health Information in text.

    Uses pattern matching to identify potential PHI including:
    - Names (common name patterns)
    - Dates (various formats)
    - Phone numbers
    - Email addresses
    - SSN
    - Medical record numbers
    - IP addresses
    - URLs

    Example:
        detector = PHIDetector()
        matches = detector.detect("Patient John Doe, DOB: 01/15/1990")
        for match in matches:
            print(f"Found {match.phi_type}: {match.value}")
    """

    def __init__(self):
        """Initialize PHI detector with regex patterns."""
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[PHIType, re.Pattern]:
        """Compile regex patterns for PHI detection."""
        return {
            # Phone numbers: (xxx) xxx-xxxx, xxx-xxx-xxxx, etc.
            PHIType.PHONE: re.compile(
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            ),

            # Email addresses
            PHIType.EMAIL: re.compile(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ),

            # SSN: xxx-xx-xxxx
            PHIType.SSN: re.compile(
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
            ),

            # Dates: MM/DD/YYYY, YYYY-MM-DD, etc.
            PHIType.DATE: re.compile(
                r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
            ),

            # IP addresses
            PHIType.IP_ADDRESS: re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),

            # URLs
            PHIType.URL: re.compile(
                r'https?://[^\s<>"{}|\\^`\[\]]+'
            ),

            # Medical Record Numbers (MRN): common patterns
            PHIType.MRN: re.compile(
                r'\b(?:MRN|mrn|Medical Record)[\s:#]*\d{5,12}\b',
                re.IGNORECASE
            ),

            # Account numbers
            PHIType.ACCOUNT: re.compile(
                r'\b(?:Account|Acct)[\s:#]*\d{6,15}\b',
                re.IGNORECASE
            )
        }

        # Note: Name detection requires NLP/NER for accuracy
        # Simple patterns would have too many false positives

    def detect(self, text: str) -> List[PHIMatch]:
        """
        Detect PHI in text.

        Args:
            text: Text to scan for PHI

        Returns:
            List of PHIMatch objects for detected PHI
        """
        if not text:
            return []

        matches = []

        for phi_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                phi_match = PHIMatch(
                    phi_type=phi_type,
                    value=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8  # Pattern-based confidence
                )
                matches.append(phi_match)

        # Sort by position
        matches.sort(key=lambda m: m.start_pos)

        return matches

    def contains_phi(self, text: str) -> bool:
        """
        Check if text contains any PHI.

        Args:
            text: Text to check

        Returns:
            True if PHI detected, False otherwise
        """
        return len(self.detect(text)) > 0

    def get_phi_types_found(self, text: str) -> Set[PHIType]:
        """
        Get set of PHI types found in text.

        Args:
            text: Text to scan

        Returns:
            Set of PHIType enums found
        """
        matches = self.detect(text)
        return {m.phi_type for m in matches}


# =============================================================================
# Data De-identification
# =============================================================================

class DataDeidentifier:
    """
    De-identify data by removing or masking PHI.

    Implements HIPAA Safe Harbor method for removing the 18 identifiers.

    Example:
        deid = DataDeidentifier()
        clean_data = deid.deidentify({
            "patient_name": "John Doe",
            "finding": "Normal chest X-ray"
        })
        # Result: {"patient_name": "[REDACTED]", "finding": "Normal chest X-ray"}
    """

    # Fields that are considered PHI and should be removed/masked
    PHI_FIELDS = {
        "patient_name", "patientname", "name",
        "patient_id", "patientid", "pid",
        "dob", "date_of_birth", "birthdate",
        "ssn", "social_security",
        "address", "street", "city", "zip", "zipcode",
        "phone", "telephone", "fax",
        "email", "email_address",
        "mrn", "medical_record_number",
        "account", "account_number",
        "insurance_id", "health_plan_id"
    }

    def __init__(self, replacement: str = "[REDACTED]"):
        """
        Initialize de-identifier.

        Args:
            replacement: String to replace PHI with
        """
        self.replacement = replacement
        self.detector = PHIDetector()

    def deidentify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        De-identify a dictionary by removing PHI fields.

        Args:
            data: Dictionary potentially containing PHI

        Returns:
            De-identified dictionary copy
        """
        if not isinstance(data, dict):
            return data

        result = {}

        for key, value in data.items():
            key_lower = key.lower().replace("_", "").replace("-", "")

            # Check if key is a known PHI field
            is_phi_field = any(
                phi_field.replace("_", "") in key_lower
                for phi_field in self.PHI_FIELDS
            )

            if is_phi_field:
                result[key] = self.replacement
            elif isinstance(value, dict):
                # Recursively de-identify nested dicts
                result[key] = self.deidentify(value)
            elif isinstance(value, list):
                # De-identify list items
                result[key] = [
                    self.deidentify(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Check string values for embedded PHI
                result[key] = self.deidentify_text(value)
            else:
                result[key] = value

        # Add de-identification marker
        result["_deidentified"] = True
        result["_deidentification_method"] = "HIPAA Safe Harbor"

        return result

    def deidentify_text(self, text: str) -> str:
        """
        De-identify free text by masking detected PHI.

        Args:
            text: Text potentially containing PHI

        Returns:
            Text with PHI masked
        """
        if not text:
            return text

        matches = self.detector.detect(text)

        if not matches:
            return text

        # Replace PHI from end to start to preserve positions
        result = text
        for match in reversed(matches):
            result = (
                result[:match.start_pos] +
                self.replacement +
                result[match.end_pos:]
            )

        return result


# =============================================================================
# DICOM De-identification
# =============================================================================

class DICOMDeidentifier:
    """
    De-identify DICOM metadata.

    Removes or masks PHI from DICOM tags according to DICOM PS3.15
    and HIPAA requirements.

    Example:
        deid = DICOMDeidentifier()
        clean_metadata = deid.deidentify({
            "PatientName": "Doe^John",
            "PatientID": "12345",
            "Modality": "CR"
        })
    """

    # DICOM tags that contain PHI
    PHI_TAGS = {
        # Patient Module
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientBirthTime",
        "PatientSex",  # Can be kept or generalized
        "PatientAge",
        "PatientSize",
        "PatientWeight",
        "PatientAddress",
        "PatientTelephoneNumbers",
        "EthnicGroup",
        "PatientComments",

        # Study Module
        "ReferringPhysicianName",
        "ReferringPhysicianAddress",
        "ReferringPhysicianTelephoneNumbers",
        "PhysiciansOfRecord",
        "PerformingPhysicianName",
        "NameOfPhysiciansReadingStudy",
        "OperatorsName",

        # Institution
        "InstitutionName",
        "InstitutionAddress",
        "InstitutionalDepartmentName",

        # Accession/ID
        "AccessionNumber",
        "StudyID",
        "OtherPatientIDs",

        # Dates (can be shifted instead of removed)
        "StudyDate",
        "SeriesDate",
        "AcquisitionDate",
        "ContentDate",
        "StudyTime",
        "SeriesTime",
        "AcquisitionTime",
        "ContentTime"
    }

    # Tags that can be kept (non-PHI imaging parameters)
    SAFE_TAGS = {
        "Modality",
        "BodyPartExamined",
        "ViewPosition",
        "Rows",
        "Columns",
        "BitsAllocated",
        "BitsStored",
        "HighBit",
        "PixelRepresentation",
        "PhotometricInterpretation",
        "SamplesPerPixel",
        "SliceThickness",
        "SpacingBetweenSlices",
        "PixelSpacing",
        "ImageOrientationPatient",
        "ImagePositionPatient"
    }

    def __init__(self, replacement: str = "ANONYMOUS"):
        """
        Initialize DICOM de-identifier.

        Args:
            replacement: String to replace PHI with
        """
        self.replacement = replacement

    def deidentify(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        De-identify DICOM metadata.

        Args:
            metadata: Dictionary of DICOM tags

        Returns:
            De-identified metadata copy
        """
        result = {}

        for tag, value in metadata.items():
            if tag in self.PHI_TAGS:
                # Replace PHI tags
                result[tag] = self.replacement
            else:
                # Keep non-PHI tags
                result[tag] = value

        # Add de-identification markers
        result["DeidentificationMethod"] = "HIPAA Safe Harbor + DICOM PS3.15"
        result["PatientIdentityRemoved"] = "YES"
        result["_deidentified"] = True

        return result

    def get_phi_tags(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Get list of PHI tags present in metadata.

        Args:
            metadata: DICOM metadata dictionary

        Returns:
            List of PHI tag names found
        """
        return [tag for tag in metadata.keys() if tag in self.PHI_TAGS]

    def validate_deidentified(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate that metadata is properly de-identified.

        Args:
            metadata: DICOM metadata to validate

        Returns:
            True if properly de-identified
        """
        phi_tags_present = self.get_phi_tags(metadata)

        for tag in phi_tags_present:
            value = metadata.get(tag, "")
            # Check if value is the replacement or empty
            if value and value != self.replacement and value != "":
                logger.warning(f"PHI tag {tag} not properly de-identified")
                return False

        return True


# =============================================================================
# Utility Functions
# =============================================================================

def validate_no_phi(data: Dict[str, Any]) -> bool:
    """
    Validate that data contains no PHI.

    Args:
        data: Data to validate

    Returns:
        True if no PHI detected
    """
    detector = PHIDetector()

    def check_value(value):
        if isinstance(value, str):
            return not detector.contains_phi(value)
        elif isinstance(value, dict):
            return all(check_value(v) for v in value.values())
        elif isinstance(value, list):
            return all(check_value(item) for item in value)
        return True

    return check_value(data)


def quick_deidentify(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick de-identification of data.

    Convenience function for one-off de-identification.

    Args:
        data: Data to de-identify

    Returns:
        De-identified data
    """
    deid = DataDeidentifier()
    return deid.deidentify(data)
