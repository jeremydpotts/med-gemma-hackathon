"""
Medical Utilities for RadAssist Pro.

Provides medical domain-specific utilities:
- Medical terminology
- ICD-10 code mapping
- FHIR resource generation
- Clinical validation helpers
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Medical Terminology
# =============================================================================

# Common radiological findings
CHEST_XRAY_FINDINGS = {
    # Normal findings
    "normal_heart_size": "Heart size is within normal limits",
    "clear_lungs": "Lungs are clear bilaterally without focal consolidation",
    "no_effusion": "No pleural effusion identified",
    "no_pneumothorax": "No pneumothorax",
    "normal_mediastinum": "Mediastinal contours are unremarkable",
    "intact_bones": "Osseous structures are intact",

    # Abnormal findings
    "cardiomegaly": "Cardiomegaly is present",
    "pulmonary_edema": "Findings consistent with pulmonary edema",
    "pneumonia": "Opacity consistent with pneumonia",
    "pleural_effusion": "Pleural effusion identified",
    "pneumothorax": "Pneumothorax identified",
    "nodule": "Pulmonary nodule identified",
    "mass": "Mass lesion identified",
    "atelectasis": "Atelectasis present",
    "consolidation": "Consolidation present"
}

# Anatomy terms
CHEST_ANATOMY = [
    "right upper lobe", "right middle lobe", "right lower lobe",
    "left upper lobe", "left lower lobe", "lingula",
    "right hilum", "left hilum", "mediastinum",
    "right hemidiaphragm", "left hemidiaphragm",
    "cardiophrenic angle", "costophrenic angle",
    "aortic arch", "descending aorta", "trachea",
    "right atrium", "left ventricle"
]

# Critical findings requiring urgent attention
CRITICAL_FINDINGS = [
    "tension pneumothorax",
    "aortic dissection",
    "pulmonary embolism",
    "large pleural effusion",
    "complete lung collapse",
    "widened mediastinum",
    "free air under diaphragm"
]


# =============================================================================
# ICD-10 Code Mapping
# =============================================================================

@dataclass
class ICD10Code:
    """Represents an ICD-10 diagnosis code."""
    code: str
    description: str
    category: str


# Common radiology-related ICD-10 codes
ICD10_CODES: Dict[str, ICD10Code] = {
    "cardiomegaly": ICD10Code("I51.7", "Cardiomegaly", "Cardiovascular"),
    "pneumonia": ICD10Code("J18.9", "Pneumonia, unspecified organism", "Respiratory"),
    "pleural_effusion": ICD10Code("J90", "Pleural effusion, not elsewhere classified", "Respiratory"),
    "pneumothorax": ICD10Code("J93.9", "Pneumothorax, unspecified", "Respiratory"),
    "pulmonary_nodule": ICD10Code("R91.1", "Solitary pulmonary nodule", "Abnormal findings"),
    "atelectasis": ICD10Code("J98.11", "Atelectasis", "Respiratory"),
    "pulmonary_edema": ICD10Code("J81.1", "Chronic pulmonary edema", "Respiratory"),
    "lung_mass": ICD10Code("R91.8", "Other nonspecific abnormal finding of lung field", "Abnormal findings"),
    "normal_chest": ICD10Code("Z87.01", "Personal history of pneumonia (recurrent)", "Factors")
}


def get_icd10_codes(findings: List[str]) -> List[ICD10Code]:
    """
    Map findings to ICD-10 codes.

    Args:
        findings: List of finding strings

    Returns:
        List of matching ICD10Code objects
    """
    codes = []
    findings_lower = [f.lower() for f in findings]

    for keyword, code in ICD10_CODES.items():
        for finding in findings_lower:
            if keyword.replace("_", " ") in finding:
                codes.append(code)
                break

    return codes


# =============================================================================
# FHIR Resource Generation
# =============================================================================

def create_fhir_diagnostic_report(
    findings: List[str],
    impression: str,
    patient_id: str = "ANONYMOUS",
    study_id: str = "",
    confidence: float = 0.0,
    model_version: str = "unknown"
) -> Dict[str, Any]:
    """
    Create a FHIR DiagnosticReport resource.

    Args:
        findings: List of findings
        impression: Overall impression
        patient_id: Patient identifier
        study_id: Study identifier
        confidence: AI confidence score
        model_version: Model version used

    Returns:
        FHIR DiagnosticReport resource as dictionary
    """
    now = datetime.utcnow().isoformat() + "Z"

    # Get ICD-10 codes
    icd_codes = get_icd10_codes(findings)

    # Build conclusion codes
    conclusion_codes = []
    for code in icd_codes:
        conclusion_codes.append({
            "coding": [{
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": code.code,
                "display": code.description
            }]
        })

    return {
        "resourceType": "DiagnosticReport",
        "id": study_id or f"report-{now.replace(':', '-')}",
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "RAD",
                "display": "Radiology"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "18748-4",
                "display": "Diagnostic imaging study"
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": patient_id
        },
        "effectiveDateTime": now,
        "issued": now,
        "conclusion": impression,
        "conclusionCode": conclusion_codes,
        "extension": [
            {
                "url": "http://radassist.ai/fhir/StructureDefinition/ai-confidence",
                "valueDecimal": round(confidence, 3)
            },
            {
                "url": "http://radassist.ai/fhir/StructureDefinition/ai-model",
                "valueString": model_version
            },
            {
                "url": "http://radassist.ai/fhir/StructureDefinition/ai-disclaimer",
                "valueString": "AI-generated report. For research purposes only. Not for clinical use."
            }
        ],
        "presentedForm": [{
            "contentType": "text/plain",
            "data": _encode_findings(findings)
        }]
    }


def _encode_findings(findings: List[str]) -> str:
    """Encode findings as base64 for FHIR."""
    import base64
    text = "\n".join(findings)
    return base64.b64encode(text.encode()).decode()


def create_fhir_observation(
    finding: str,
    body_site: Optional[str] = None,
    patient_id: str = "ANONYMOUS"
) -> Dict[str, Any]:
    """
    Create a FHIR Observation resource for a single finding.

    Args:
        finding: The finding text
        body_site: Optional anatomical location
        patient_id: Patient identifier

    Returns:
        FHIR Observation resource
    """
    now = datetime.utcnow().isoformat() + "Z"

    observation = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "18782-3",
                "display": "Radiology Study observation"
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": now,
        "valueString": finding
    }

    if body_site:
        observation["bodySite"] = {
            "text": body_site
        }

    return observation


# =============================================================================
# Clinical Validation
# =============================================================================

def validate_findings_clinically(findings: List[str]) -> Dict[str, Any]:
    """
    Validate that findings are clinically reasonable.

    Checks for:
    - Contradictory findings
    - Implausible combinations
    - Missing expected findings

    Args:
        findings: List of findings to validate

    Returns:
        Validation result dictionary
    """
    findings_lower = [f.lower() for f in findings]
    issues = []
    warnings = []

    # Check for contradictions
    contradictions = [
        ("normal heart size", "cardiomegaly"),
        ("clear lungs", "pneumonia"),
        ("no pleural effusion", "pleural effusion"),
        ("no pneumothorax", "pneumothorax")
    ]

    for finding1, finding2 in contradictions:
        has_first = any(finding1 in f for f in findings_lower)
        has_second = any(finding2 in f for f in findings_lower)

        if has_first and has_second:
            issues.append(f"Contradictory findings: '{finding1}' and '{finding2}'")

    # Check for missing standard findings
    standard_checks = ["heart", "lung", "pleural", "mediastin"]
    for check in standard_checks:
        if not any(check in f for f in findings_lower):
            warnings.append(f"No findings mentioning '{check}'")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "findings_count": len(findings)
    }


def is_critical_finding(finding: str) -> bool:
    """
    Check if finding is critical/urgent.

    Args:
        finding: Finding text

    Returns:
        True if finding is critical
    """
    finding_lower = finding.lower()
    return any(critical in finding_lower for critical in CRITICAL_FINDINGS)


def classify_finding_severity(finding: str) -> str:
    """
    Classify finding severity.

    Args:
        finding: Finding text

    Returns:
        Severity level: "critical", "abnormal", "normal", or "incidental"
    """
    finding_lower = finding.lower()

    # Check for critical
    if is_critical_finding(finding):
        return "critical"

    # Check for clearly normal
    normal_indicators = ["normal", "unremarkable", "clear", "no evidence", "negative"]
    if any(indicator in finding_lower for indicator in normal_indicators):
        return "normal"

    # Check for abnormal
    abnormal_indicators = [
        "opacity", "infiltrate", "nodule", "mass", "effusion",
        "enlargement", "cardiomegaly", "consolidation", "atelectasis"
    ]
    if any(indicator in finding_lower for indicator in abnormal_indicators):
        return "abnormal"

    return "incidental"


# =============================================================================
# Report Formatting
# =============================================================================

def format_structured_report(
    findings: List[str],
    impression: str,
    patient_info: Optional[Dict[str, str]] = None,
    study_info: Optional[Dict[str, str]] = None
) -> str:
    """
    Format findings as a structured radiology report.

    Args:
        findings: List of findings
        impression: Overall impression
        patient_info: Optional patient information
        study_info: Optional study information

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("RADIOLOGY REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Patient info
    if patient_info:
        lines.append("PATIENT INFORMATION:")
        for key, value in patient_info.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    # Study info
    if study_info:
        lines.append("STUDY INFORMATION:")
        for key, value in study_info.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    # Findings
    lines.append("-" * 70)
    lines.append("FINDINGS:")
    lines.append("-" * 70)
    for i, finding in enumerate(findings, 1):
        severity = classify_finding_severity(finding)
        prefix = "⚠️ " if severity == "critical" else ""
        lines.append(f"  {i}. {prefix}{finding}")

    lines.append("")

    # Impression
    lines.append("-" * 70)
    lines.append("IMPRESSION:")
    lines.append("-" * 70)
    lines.append(f"  {impression}")

    # Footer
    lines.append("")
    lines.append("=" * 70)
    lines.append("⚠️ AI-GENERATED - FOR RESEARCH PURPOSES ONLY")
    lines.append("This report must be verified by a qualified radiologist.")
    lines.append("=" * 70)

    return "\n".join(lines)


# =============================================================================
# Measurement Utilities
# =============================================================================

def format_measurement(value: float, unit: str, precision: int = 1) -> str:
    """
    Format a measurement with unit.

    Args:
        value: Numeric value
        unit: Unit of measurement
        precision: Decimal places

    Returns:
        Formatted measurement string
    """
    return f"{value:.{precision}f} {unit}"


def cardiothoracic_ratio_assessment(ratio: float) -> Tuple[str, str]:
    """
    Assess cardiothoracic ratio.

    Args:
        ratio: CT ratio value

    Returns:
        Tuple of (assessment, description)
    """
    if ratio < 0.5:
        return "normal", f"CT ratio {ratio:.2f} is within normal limits (<0.5)"
    elif ratio < 0.55:
        return "borderline", f"CT ratio {ratio:.2f} is borderline enlarged (0.5-0.55)"
    else:
        return "enlarged", f"CT ratio {ratio:.2f} indicates cardiomegaly (>0.55)"


def lung_volume_assessment(volume_ml: float, predicted_ml: float) -> Tuple[str, str]:
    """
    Assess lung volume compared to predicted.

    Args:
        volume_ml: Measured volume in mL
        predicted_ml: Predicted normal volume

    Returns:
        Tuple of (assessment, description)
    """
    ratio = volume_ml / predicted_ml if predicted_ml > 0 else 1.0

    if ratio >= 0.8:
        return "normal", f"Lung volume {volume_ml:.0f} mL ({ratio:.0%} of predicted)"
    elif ratio >= 0.6:
        return "mildly_reduced", f"Mildly reduced lung volume {volume_ml:.0f} mL ({ratio:.0%} of predicted)"
    else:
        return "significantly_reduced", f"Significantly reduced lung volume {volume_ml:.0f} mL ({ratio:.0%} of predicted)"
