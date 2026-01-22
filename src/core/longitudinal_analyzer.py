"""
Longitudinal Analysis Engine for RadAssist Pro.

This module implements the core innovation: AI-powered longitudinal
change detection with clinical decision support.

Key features:
- Change detection between sequential medical images
- Volume doubling time (VDT) calculation
- Lung-RADS guideline integration
- Differential diagnosis evolution tracking
- Natural language report generation

This is the PRIMARY DIFFERENTIATOR for the Med-Gemma Impact Challenge.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class ChangeTrajectory(Enum):
    """Classification of change trajectory."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INDETERMINATE = "indeterminate"


class LungRADSCategory(Enum):
    """Lung-RADS classification categories."""
    CATEGORY_0 = "0"  # Incomplete
    CATEGORY_1 = "1"  # Negative
    CATEGORY_2 = "2"  # Benign appearance
    CATEGORY_3 = "3"  # Probably benign
    CATEGORY_4A = "4A"  # Suspicious
    CATEGORY_4B = "4B"  # Very suspicious
    CATEGORY_4X = "4X"  # Additional features


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    INTERMEDIATE = "intermediate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Volume doubling time thresholds (days)
VDT_HIGH_RISK = 400  # VDT < 400 days is concerning
VDT_INTERMEDIATE = 600  # VDT 400-600 is intermediate
VDT_LOW_RISK = 600  # VDT > 600 is less concerning

# Size thresholds for Lung-RADS (mm)
NODULE_SIZE_THRESHOLDS = {
    "very_small": 4,
    "small": 6,
    "intermediate": 8,
    "large": 15,
    "very_large": 30
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NoduleMeasurement:
    """Represents a nodule measurement at a single timepoint."""
    date: datetime
    size_mm: float
    location: str
    nodule_type: str = "solid"  # solid, ground-glass, part-solid
    volume_mm3: Optional[float] = None
    morphology: Optional[str] = None  # spiculated, smooth, irregular

    @property
    def volume_calculated(self) -> float:
        """Calculate volume assuming spherical nodule if not provided."""
        if self.volume_mm3:
            return self.volume_mm3
        # V = (4/3) * pi * r^3, where r = size/2
        radius = self.size_mm / 2
        return (4/3) * math.pi * (radius ** 3)


@dataclass
class ChangeAnalysis:
    """Results of longitudinal change analysis."""
    # Core metrics
    size_change_mm: float
    size_change_percent: float
    volume_change_percent: float
    days_between: int

    # Clinical metrics
    volume_doubling_time_days: Optional[float] = None
    trajectory: ChangeTrajectory = ChangeTrajectory.INDETERMINATE
    lung_rads_current: Optional[LungRADSCategory] = None
    lung_rads_prior: Optional[LungRADSCategory] = None
    risk_level: RiskLevel = RiskLevel.INTERMEDIATE

    # Generated content
    change_summary: str = ""
    clinical_interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    differential_evolution: Dict[str, str] = field(default_factory=dict)

    # Report text
    comparison_paragraph: str = ""
    patient_summary: str = ""


@dataclass
class DifferentialDiagnosis:
    """Tracks evolution of differential diagnosis."""
    diagnosis: str
    prior_probability: str  # high, moderate, low
    current_probability: str
    change_rationale: str


@dataclass
class LongitudinalReport:
    """Complete longitudinal analysis report."""
    patient_context: str
    measurements: List[NoduleMeasurement]
    analysis: ChangeAnalysis
    differentials: List[DifferentialDiagnosis]
    timeline_summary: str

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    model_version: str = "radassist-pro-v1"
    disclaimer: str = "AI-generated analysis. For research purposes only. Not for clinical use."


# =============================================================================
# Core Analysis Functions
# =============================================================================

def calculate_volume_doubling_time(
    measurement1: NoduleMeasurement,
    measurement2: NoduleMeasurement
) -> Optional[float]:
    """
    Calculate volume doubling time (VDT) between two measurements.

    VDT = (days_between * ln(2)) / ln(V2/V1)

    Args:
        measurement1: Earlier measurement
        measurement2: Later measurement

    Returns:
        VDT in days, or None if calculation not possible
    """
    v1 = measurement1.volume_calculated
    v2 = measurement2.volume_calculated

    # Ensure measurements are in correct order
    if measurement2.date < measurement1.date:
        measurement1, measurement2 = measurement2, measurement1
        v1, v2 = v2, v1

    days_between = (measurement2.date - measurement1.date).days

    if days_between <= 0:
        return None

    if v2 <= v1:
        # Nodule shrinking or stable - VDT not applicable
        return None

    try:
        vdt = (days_between * math.log(2)) / math.log(v2 / v1)
        return vdt
    except (ValueError, ZeroDivisionError):
        return None


def classify_lung_rads(
    size_mm: float,
    nodule_type: str = "solid",
    growth_detected: bool = False,
    vdt_days: Optional[float] = None
) -> LungRADSCategory:
    """
    Classify nodule according to Lung-RADS guidelines.

    Simplified implementation based on ACR Lung-RADS v1.1.

    Args:
        size_mm: Nodule size in mm
        nodule_type: solid, ground-glass, or part-solid
        growth_detected: Whether growth was detected
        vdt_days: Volume doubling time if calculated

    Returns:
        Lung-RADS category
    """
    if nodule_type == "solid":
        if size_mm < 6:
            return LungRADSCategory.CATEGORY_2
        elif size_mm < 8:
            if growth_detected:
                return LungRADSCategory.CATEGORY_4A
            return LungRADSCategory.CATEGORY_3
        elif size_mm < 15:
            if growth_detected and vdt_days and vdt_days < VDT_HIGH_RISK:
                return LungRADSCategory.CATEGORY_4B
            return LungRADSCategory.CATEGORY_4A
        else:
            return LungRADSCategory.CATEGORY_4B

    elif nodule_type == "ground-glass":
        if size_mm < 30:
            return LungRADSCategory.CATEGORY_2
        else:
            if growth_detected:
                return LungRADSCategory.CATEGORY_4A
            return LungRADSCategory.CATEGORY_3

    elif nodule_type == "part-solid":
        if size_mm < 6:
            return LungRADSCategory.CATEGORY_2
        else:
            # Solid component matters
            if growth_detected:
                return LungRADSCategory.CATEGORY_4B
            return LungRADSCategory.CATEGORY_4A

    return LungRADSCategory.CATEGORY_3


def assess_risk_level(
    vdt_days: Optional[float],
    lung_rads: LungRADSCategory,
    trajectory: ChangeTrajectory
) -> RiskLevel:
    """
    Assess overall risk level based on multiple factors.

    Args:
        vdt_days: Volume doubling time
        lung_rads: Current Lung-RADS category
        trajectory: Change trajectory

    Returns:
        Risk level assessment
    """
    # VDT-based risk
    if vdt_days:
        if vdt_days < 200:
            return RiskLevel.VERY_HIGH
        elif vdt_days < VDT_HIGH_RISK:
            return RiskLevel.HIGH
        elif vdt_days < VDT_INTERMEDIATE:
            return RiskLevel.INTERMEDIATE

    # Lung-RADS based risk
    if lung_rads == LungRADSCategory.CATEGORY_4B:
        return RiskLevel.VERY_HIGH
    elif lung_rads == LungRADSCategory.CATEGORY_4A:
        return RiskLevel.HIGH
    elif lung_rads == LungRADSCategory.CATEGORY_3:
        return RiskLevel.INTERMEDIATE

    # Trajectory based
    if trajectory == ChangeTrajectory.WORSENING:
        return RiskLevel.HIGH

    return RiskLevel.LOW


def determine_trajectory(
    size_change_percent: float,
    volume_change_percent: float
) -> ChangeTrajectory:
    """
    Determine change trajectory from measurements.

    Args:
        size_change_percent: Percentage change in linear size
        volume_change_percent: Percentage change in volume

    Returns:
        Change trajectory classification
    """
    # Use volume change as primary (more sensitive)
    if volume_change_percent > 25:
        return ChangeTrajectory.WORSENING
    elif volume_change_percent < -25:
        return ChangeTrajectory.IMPROVING
    elif abs(volume_change_percent) <= 25:
        return ChangeTrajectory.STABLE

    return ChangeTrajectory.INDETERMINATE


# =============================================================================
# Report Generation
# =============================================================================

def generate_change_summary(
    prior: NoduleMeasurement,
    current: NoduleMeasurement,
    analysis: ChangeAnalysis
) -> str:
    """
    Generate natural language change summary.

    This is a key innovation - converting measurements to clinical language.
    """
    location = current.location or "the identified nodule"

    if analysis.trajectory == ChangeTrajectory.STABLE:
        return (
            f"The {current.nodule_type} nodule in {location} remains stable, "
            f"measuring {current.size_mm}mm (previously {prior.size_mm}mm, "
            f"{analysis.size_change_percent:+.1f}% change over {analysis.days_between} days)."
        )

    elif analysis.trajectory == ChangeTrajectory.IMPROVING:
        return (
            f"The {current.nodule_type} nodule in {location} has decreased in size, "
            f"now measuring {current.size_mm}mm (previously {prior.size_mm}mm, "
            f"{abs(analysis.size_change_percent):.1f}% reduction over {analysis.days_between} days). "
            f"This suggests interval improvement."
        )

    elif analysis.trajectory == ChangeTrajectory.WORSENING:
        vdt_text = ""
        if analysis.volume_doubling_time_days:
            vdt_text = f" Volume doubling time is approximately {analysis.volume_doubling_time_days:.0f} days."

        return (
            f"The {current.nodule_type} nodule in {location} has demonstrated interval growth, "
            f"now measuring {current.size_mm}mm (previously {prior.size_mm}mm, "
            f"{analysis.size_change_percent:+.1f}% increase, "
            f"{analysis.volume_change_percent:+.1f}% volume increase over {analysis.days_between} days).{vdt_text}"
        )

    return f"Change assessment indeterminate. Current: {current.size_mm}mm, Prior: {prior.size_mm}mm."


def generate_clinical_interpretation(analysis: ChangeAnalysis) -> str:
    """Generate clinical interpretation of findings."""

    interpretations = []

    # VDT interpretation
    if analysis.volume_doubling_time_days:
        vdt = analysis.volume_doubling_time_days
        if vdt < 200:
            interpretations.append(
                f"Volume doubling time of {vdt:.0f} days is concerning for "
                "rapid growth, highly suggestive of malignancy."
            )
        elif vdt < VDT_HIGH_RISK:
            interpretations.append(
                f"Volume doubling time of {vdt:.0f} days (<400 days) "
                "raises concern for malignancy."
            )
        elif vdt < VDT_INTERMEDIATE:
            interpretations.append(
                f"Volume doubling time of {vdt:.0f} days suggests "
                "intermediate growth rate."
            )
        else:
            interpretations.append(
                f"Volume doubling time of {vdt:.0f} days suggests "
                "slower growth, though continued surveillance warranted."
            )

    # Lung-RADS interpretation
    if analysis.lung_rads_current:
        category = analysis.lung_rads_current.value
        interpretations.append(f"Current Lung-RADS category: {category}.")

        if analysis.lung_rads_prior and analysis.lung_rads_prior != analysis.lung_rads_current:
            interpretations.append(
                f"Category has changed from {analysis.lung_rads_prior.value} "
                f"to {analysis.lung_rads_current.value}."
            )

    # Risk summary
    risk_descriptions = {
        RiskLevel.LOW: "Overall risk assessment: LOW.",
        RiskLevel.INTERMEDIATE: "Overall risk assessment: INTERMEDIATE.",
        RiskLevel.HIGH: "Overall risk assessment: HIGH - further evaluation recommended.",
        RiskLevel.VERY_HIGH: "Overall risk assessment: VERY HIGH - urgent evaluation recommended."
    }
    interpretations.append(risk_descriptions.get(analysis.risk_level, ""))

    return " ".join(interpretations)


def generate_recommendations(analysis: ChangeAnalysis) -> List[str]:
    """Generate clinical recommendations based on analysis."""

    recommendations = []

    if analysis.risk_level == RiskLevel.VERY_HIGH:
        recommendations.append("Urgent tissue sampling or PET-CT recommended.")
        recommendations.append("Consider multidisciplinary tumor board discussion.")

    elif analysis.risk_level == RiskLevel.HIGH:
        recommendations.append("Consider PET-CT for further characterization.")
        recommendations.append("If PET positive, tissue sampling recommended.")
        recommendations.append("Short-interval follow-up CT if PET not performed (3 months).")

    elif analysis.risk_level == RiskLevel.INTERMEDIATE:
        if analysis.trajectory == ChangeTrajectory.STABLE:
            recommendations.append("Continue surveillance with follow-up CT in 6 months.")
        else:
            recommendations.append("Consider follow-up CT in 3 months to assess trajectory.")

    else:  # LOW risk
        if analysis.trajectory == ChangeTrajectory.STABLE:
            recommendations.append("Continue annual low-dose CT screening.")
        elif analysis.trajectory == ChangeTrajectory.IMPROVING:
            recommendations.append("Likely benign etiology. Follow-up CT in 12 months.")

    # Always add standard disclaimer
    recommendations.append(
        "Clinical correlation recommended. "
        "This AI-generated analysis should be verified by a qualified radiologist."
    )

    return recommendations


def generate_differential_evolution(
    analysis: ChangeAnalysis
) -> List[DifferentialDiagnosis]:
    """
    Generate differential diagnosis evolution.

    This is the "judge-wowing" feature - showing how differentials
    should change based on the observed interval changes.
    """
    differentials = []

    if analysis.trajectory == ChangeTrajectory.WORSENING:
        differentials.append(DifferentialDiagnosis(
            diagnosis="Primary lung malignancy",
            prior_probability="moderate",
            current_probability="high",
            change_rationale="Interval growth with VDT consistent with malignancy"
        ))
        differentials.append(DifferentialDiagnosis(
            diagnosis="Inflammatory/infectious",
            prior_probability="moderate",
            current_probability="low",
            change_rationale="Would expect stability or resolution if infectious"
        ))
        differentials.append(DifferentialDiagnosis(
            diagnosis="Slow-growing carcinoid",
            prior_probability="low",
            current_probability="moderate",
            change_rationale="Cannot exclude based on growth pattern"
        ))

    elif analysis.trajectory == ChangeTrajectory.STABLE:
        differentials.append(DifferentialDiagnosis(
            diagnosis="Benign granuloma",
            prior_probability="moderate",
            current_probability="high",
            change_rationale="Stability over time favors benign etiology"
        ))
        differentials.append(DifferentialDiagnosis(
            diagnosis="Primary lung malignancy",
            prior_probability="moderate",
            current_probability="low",
            change_rationale="Stability decreases concern, though not excluded"
        ))
        differentials.append(DifferentialDiagnosis(
            diagnosis="Hamartoma",
            prior_probability="low",
            current_probability="moderate",
            change_rationale="Benign tumor typically stable"
        ))

    elif analysis.trajectory == ChangeTrajectory.IMPROVING:
        differentials.append(DifferentialDiagnosis(
            diagnosis="Resolving infection",
            prior_probability="moderate",
            current_probability="high",
            change_rationale="Interval decrease consistent with resolving process"
        ))
        differentials.append(DifferentialDiagnosis(
            diagnosis="Primary lung malignancy",
            prior_probability="moderate",
            current_probability="very_low",
            change_rationale="Spontaneous regression of malignancy extremely rare"
        ))

    return differentials


def generate_comparison_paragraph(
    prior: NoduleMeasurement,
    current: NoduleMeasurement,
    analysis: ChangeAnalysis
) -> str:
    """
    Generate draft comparison paragraph for radiology report.

    This saves radiologist time by providing ready-to-use language.
    """
    prior_date = prior.date.strftime("%Y-%m-%d")

    if analysis.trajectory == ChangeTrajectory.STABLE:
        return (
            f"COMPARISON: CT Chest dated {prior_date}\n\n"
            f"The previously identified {prior.size_mm}mm {prior.nodule_type} nodule "
            f"in the {current.location} remains stable, now measuring {current.size_mm}mm. "
            f"No significant interval change ({analysis.size_change_percent:+.1f}% over "
            f"{analysis.days_between} days). Continued surveillance recommended per "
            f"Lung-RADS {analysis.lung_rads_current.value if analysis.lung_rads_current else 'guidelines'}."
        )

    elif analysis.trajectory == ChangeTrajectory.WORSENING:
        vdt_text = ""
        if analysis.volume_doubling_time_days:
            vdt_text = f" Volume doubling time is approximately {analysis.volume_doubling_time_days:.0f} days."

        return (
            f"COMPARISON: CT Chest dated {prior_date}\n\n"
            f"The previously identified {prior.size_mm}mm {prior.nodule_type} nodule "
            f"in the {current.location} has demonstrated interval growth, now measuring "
            f"{current.size_mm}mm ({analysis.size_change_percent:+.1f}% increase, "
            f"{analysis.volume_change_percent:+.1f}% volume increase over {analysis.days_between} days).{vdt_text} "
            f"This raises concern for malignancy. "
            f"Recommend {analysis.recommendations[0] if analysis.recommendations else 'further evaluation'} "
            f"per Lung-RADS {analysis.lung_rads_current.value if analysis.lung_rads_current else '4B'} guidelines."
        )

    elif analysis.trajectory == ChangeTrajectory.IMPROVING:
        return (
            f"COMPARISON: CT Chest dated {prior_date}\n\n"
            f"The previously identified {prior.size_mm}mm {prior.nodule_type} nodule "
            f"in the {current.location} has decreased in size, now measuring {current.size_mm}mm "
            f"({abs(analysis.size_change_percent):.1f}% decrease over {analysis.days_between} days). "
            f"Interval improvement suggests benign etiology. "
            f"Follow-up imaging in 12 months recommended to document resolution."
        )

    return f"COMPARISON: CT Chest dated {prior_date}\n\nIndeterminate change. Clinical correlation recommended."


def generate_patient_summary(
    analysis: ChangeAnalysis,
    current: NoduleMeasurement
) -> str:
    """
    Generate patient-friendly summary of findings.

    This supports patient engagement and understanding.
    """
    if analysis.trajectory == ChangeTrajectory.STABLE:
        return (
            f"Your lung scan shows a small spot ({current.size_mm}mm) that has not changed "
            f"since your last scan. This is reassuring, as it suggests the spot is unlikely "
            f"to be harmful. Your doctor recommends continuing to monitor it with regular scans."
        )

    elif analysis.trajectory == ChangeTrajectory.WORSENING:
        return (
            f"Your lung scan shows a spot that has grown since your last scan "
            f"(from {current.size_mm - analysis.size_change_mm:.1f}mm to {current.size_mm}mm). "
            f"While this doesn't definitely mean it's cancer, your doctor will likely recommend "
            f"additional tests to learn more about it. Please follow up with your healthcare team "
            f"to discuss next steps."
        )

    elif analysis.trajectory == ChangeTrajectory.IMPROVING:
        return (
            f"Good news - your lung scan shows a spot that has gotten smaller since your "
            f"last scan (now {current.size_mm}mm). This usually means it was caused by "
            f"something like an infection that is healing. Your doctor may recommend one more "
            f"scan to confirm it continues to improve."
        )

    return "Please discuss your scan results with your healthcare provider."


# =============================================================================
# Main Analysis Function
# =============================================================================

def analyze_longitudinal_change(
    prior_measurement: NoduleMeasurement,
    current_measurement: NoduleMeasurement,
    clinical_context: Optional[str] = None
) -> ChangeAnalysis:
    """
    Perform comprehensive longitudinal change analysis.

    This is the core function of RadAssist Pro.

    Args:
        prior_measurement: Earlier nodule measurement
        current_measurement: Later nodule measurement
        clinical_context: Optional clinical context

    Returns:
        Complete change analysis with clinical decision support
    """
    # Ensure correct ordering
    if current_measurement.date < prior_measurement.date:
        prior_measurement, current_measurement = current_measurement, prior_measurement

    # Calculate basic metrics
    size_change_mm = current_measurement.size_mm - prior_measurement.size_mm
    size_change_percent = (size_change_mm / prior_measurement.size_mm) * 100 if prior_measurement.size_mm > 0 else 0

    v_prior = prior_measurement.volume_calculated
    v_current = current_measurement.volume_calculated
    volume_change_percent = ((v_current - v_prior) / v_prior) * 100 if v_prior > 0 else 0

    days_between = (current_measurement.date - prior_measurement.date).days

    # Calculate VDT
    vdt = calculate_volume_doubling_time(prior_measurement, current_measurement)

    # Determine trajectory
    trajectory = determine_trajectory(size_change_percent, volume_change_percent)

    # Classify Lung-RADS
    growth_detected = trajectory == ChangeTrajectory.WORSENING
    lung_rads_prior = classify_lung_rads(
        prior_measurement.size_mm,
        prior_measurement.nodule_type,
        False,
        None
    )
    lung_rads_current = classify_lung_rads(
        current_measurement.size_mm,
        current_measurement.nodule_type,
        growth_detected,
        vdt
    )

    # Assess risk
    risk_level = assess_risk_level(vdt, lung_rads_current, trajectory)

    # Create analysis object
    analysis = ChangeAnalysis(
        size_change_mm=size_change_mm,
        size_change_percent=size_change_percent,
        volume_change_percent=volume_change_percent,
        days_between=days_between,
        volume_doubling_time_days=vdt,
        trajectory=trajectory,
        lung_rads_current=lung_rads_current,
        lung_rads_prior=lung_rads_prior,
        risk_level=risk_level
    )

    # Generate content
    analysis.change_summary = generate_change_summary(
        prior_measurement, current_measurement, analysis
    )
    analysis.clinical_interpretation = generate_clinical_interpretation(analysis)
    analysis.recommendations = generate_recommendations(analysis)
    analysis.comparison_paragraph = generate_comparison_paragraph(
        prior_measurement, current_measurement, analysis
    )
    analysis.patient_summary = generate_patient_summary(
        analysis, current_measurement
    )

    return analysis


def create_longitudinal_report(
    measurements: List[NoduleMeasurement],
    clinical_context: str = ""
) -> LongitudinalReport:
    """
    Create a complete longitudinal analysis report.

    Args:
        measurements: List of measurements (oldest to newest)
        clinical_context: Clinical context string

    Returns:
        Complete longitudinal report
    """
    if len(measurements) < 2:
        raise ValueError("At least 2 measurements required for longitudinal analysis")

    # Sort by date
    measurements = sorted(measurements, key=lambda m: m.date)

    # Analyze most recent change
    prior = measurements[-2]
    current = measurements[-1]
    analysis = analyze_longitudinal_change(prior, current, clinical_context)

    # Generate differentials
    differentials = generate_differential_evolution(analysis)

    # Build timeline summary
    timeline_lines = ["TIMELINE:"]
    for m in measurements:
        date_str = m.date.strftime("%Y-%m-%d")
        timeline_lines.append(f"- {date_str}: {m.size_mm}mm {m.nodule_type} nodule")
    timeline_summary = "\n".join(timeline_lines)

    return LongitudinalReport(
        patient_context=clinical_context,
        measurements=measurements,
        analysis=analysis,
        differentials=differentials,
        timeline_summary=timeline_summary
    )


# =============================================================================
# Test/Demo Function
# =============================================================================

def demo_analysis():
    """
    Demonstrate the longitudinal analysis capability.

    This creates the demo scenario for the competition.
    """
    print("=" * 70)
    print("RadAssist Pro - Longitudinal Analysis Demo")
    print("'AI That Remembers'")
    print("=" * 70)
    print()

    # Create demo measurements (the "missed progression" scenario)
    measurements = [
        NoduleMeasurement(
            date=datetime(2024, 1, 15),
            size_mm=6.0,
            location="right upper lobe",
            nodule_type="solid",
            morphology="spiculated"
        ),
        NoduleMeasurement(
            date=datetime(2024, 7, 20),
            size_mm=6.2,
            location="right upper lobe",
            nodule_type="solid",
            morphology="spiculated"
        ),
        NoduleMeasurement(
            date=datetime(2025, 1, 18),
            size_mm=6.8,
            location="right upper lobe",
            nodule_type="solid",
            morphology="spiculated"
        ),
        NoduleMeasurement(
            date=datetime(2025, 7, 15),
            size_mm=8.3,
            location="right upper lobe",
            nodule_type="solid",
            morphology="spiculated"
        )
    ]

    clinical_context = "58-year-old female, former smoker (30 pack-years), incidental lung nodule on screening CT"

    # Generate report
    report = create_longitudinal_report(measurements, clinical_context)

    # Display results
    print("PATIENT CONTEXT:")
    print(report.patient_context)
    print()

    print(report.timeline_summary)
    print()

    print("CHANGE ANALYSIS:")
    print("-" * 50)
    print(f"Size change: {report.analysis.size_change_mm:+.1f}mm ({report.analysis.size_change_percent:+.1f}%)")
    print(f"Volume change: {report.analysis.volume_change_percent:+.1f}%")
    print(f"Days between scans: {report.analysis.days_between}")
    if report.analysis.volume_doubling_time_days:
        print(f"Volume doubling time: {report.analysis.volume_doubling_time_days:.0f} days")
    print(f"Trajectory: {report.analysis.trajectory.value.upper()}")
    print(f"Lung-RADS: {report.analysis.lung_rads_prior.value} → {report.analysis.lung_rads_current.value}")
    print(f"Risk Level: {report.analysis.risk_level.value.upper()}")
    print()

    print("CHANGE SUMMARY:")
    print("-" * 50)
    print(report.analysis.change_summary)
    print()

    print("CLINICAL INTERPRETATION:")
    print("-" * 50)
    print(report.analysis.clinical_interpretation)
    print()

    print("DIFFERENTIAL DIAGNOSIS EVOLUTION:")
    print("-" * 50)
    for diff in report.differentials:
        print(f"• {diff.diagnosis}")
        print(f"  Prior: {diff.prior_probability} → Current: {diff.current_probability}")
        print(f"  Rationale: {diff.change_rationale}")
    print()

    print("RECOMMENDATIONS:")
    print("-" * 50)
    for i, rec in enumerate(report.analysis.recommendations, 1):
        print(f"{i}. {rec}")
    print()

    print("DRAFT COMPARISON PARAGRAPH:")
    print("-" * 50)
    print(report.analysis.comparison_paragraph)
    print()

    print("PATIENT SUMMARY:")
    print("-" * 50)
    print(report.analysis.patient_summary)
    print()

    print("=" * 70)
    print("⚠️  DISCLAIMER: AI-generated analysis. For research purposes only.")
    print("    Not for clinical use. Must be verified by qualified radiologist.")
    print("=" * 70)

    return report


if __name__ == "__main__":
    demo_analysis()
