"""
Image Analysis Pipeline for RadAssist Pro.

This module orchestrates the complete workflow from image upload
to longitudinal analysis:

1. Image Upload → Nodule Detection → Measurements
2. Multiple Scans → Longitudinal Analysis → Clinical Decision Support
3. Results → Report Generation → Patient Summary

This is the main entry point for processing medical images.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from src.core.nodule_detector import (
    NoduleDetector,
    DetectedNodule,
    DetectionResult,
    ScanMetadata
)
from src.core.longitudinal_analyzer import (
    NoduleMeasurement,
    ChangeAnalysis,
    LongitudinalReport,
    analyze_longitudinal_change,
    create_longitudinal_report,
    generate_differential_evolution,
    RiskLevel,
    ChangeTrajectory,
    LungRADSCategory
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisPipelineConfig:
    """Configuration for the analysis pipeline."""
    min_nodule_size_mm: float = 3.0  # Minimum size to track
    model_name: str = "medgemma-1.5-4b"
    mock_mode: bool = True  # Use mock detection
    include_visualizations: bool = True


@dataclass
class PipelineResult:
    """Complete result from the analysis pipeline."""
    # Detection results for each scan
    detection_results: List[DetectionResult]

    # Longitudinal analysis (if multiple scans)
    longitudinal_report: Optional[LongitudinalReport] = None

    # Differential diagnosis evolution
    differentials: List[Any] = None

    # Summary
    nodule_count: int = 0
    scans_processed: int = 0
    processing_time_ms: float = 0.0

    # Warnings/errors
    warnings: List[str] = None
    errors: List[str] = None

    @property
    def has_longitudinal(self) -> bool:
        return self.longitudinal_report is not None

    @property
    def requires_action(self) -> bool:
        """Check if findings require clinical action."""
        if self.longitudinal_report:
            return self.longitudinal_report.analysis.risk_level in [
                RiskLevel.HIGH,
                RiskLevel.VERY_HIGH
            ]
        return False

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary dictionary of the analysis."""
        summary = {
            "scans_analyzed": self.scans_processed,
            "nodules_found": self.nodule_count,
            "has_longitudinal_data": self.has_longitudinal,
            "requires_action": self.requires_action,
        }

        if self.has_longitudinal and self.longitudinal_report:
            analysis = self.longitudinal_report.analysis
            summary.update({
                "risk_level": analysis.risk_level.value,
                "trajectory": analysis.trajectory.value,
                "size_change_percent": f"{analysis.size_change_percent:.1f}%",
                "volume_doubling_time": (
                    f"{analysis.volume_doubling_time_days:.0f} days"
                    if analysis.volume_doubling_time_days else "N/A"
                ),
                "lung_rads": (
                    analysis.lung_rads_current.value
                    if analysis.lung_rads_current else "N/A"
                ),
                "recommendations": analysis.recommendations,
            })

        if self.warnings:
            summary["warnings"] = self.warnings

        return summary


class ImageAnalysisPipeline:
    """
    Main pipeline for processing medical images through RadAssist Pro.

    This orchestrates:
    1. Image loading and preprocessing
    2. Nodule detection via MedGemma
    3. Measurement extraction
    4. Longitudinal analysis across multiple scans
    5. Clinical decision support generation
    6. Report and summary generation

    Example:
        pipeline = ImageAnalysisPipeline()

        # Single scan analysis
        result = pipeline.analyze_single("/path/to/scan.dcm")
        print(f"Found {result.nodule_count} nodules")

        # Longitudinal analysis (multiple scans)
        result = pipeline.analyze_longitudinal([
            ("/path/to/scan1.dcm", datetime(2024, 1, 15)),
            ("/path/to/scan2.dcm", datetime(2024, 7, 15)),
        ])
        print(f"Risk Level: {result.longitudinal_report.analysis.risk_level}")
    """

    def __init__(self, config: Optional[AnalysisPipelineConfig] = None, model=None):
        """
        Initialize the analysis pipeline.

        Args:
            config: Pipeline configuration
            model: Optional MedGemma model instance
        """
        self.config = config or AnalysisPipelineConfig()
        self.detector = NoduleDetector(model=model)
        self._model = model

        logger.info(f"ImageAnalysisPipeline initialized (mock_mode={self.config.mock_mode})")

    def analyze_single(
        self,
        image_path: Union[str, Path],
        scan_date: Optional[datetime] = None,
        clinical_context: Optional[str] = None
    ) -> PipelineResult:
        """
        Analyze a single scan for nodules.

        Args:
            image_path: Path to image/DICOM file
            scan_date: Date of scan
            clinical_context: Clinical history

        Returns:
            PipelineResult with detection findings
        """
        import time
        start_time = time.time()

        # Run detection
        detection_result = self.detector.detect(
            image_path,
            scan_date=scan_date,
            clinical_context=clinical_context
        )

        processing_time = (time.time() - start_time) * 1000

        return PipelineResult(
            detection_results=[detection_result],
            nodule_count=detection_result.nodule_count,
            scans_processed=1,
            processing_time_ms=processing_time,
            warnings=[],
            errors=[]
        )

    def analyze_longitudinal(
        self,
        scans: List[Tuple[Union[str, Path], datetime]],
        clinical_context: Optional[str] = None,
        nodule_location: Optional[str] = None
    ) -> PipelineResult:
        """
        Perform longitudinal analysis across multiple scans.

        This is the PRIMARY FEATURE of RadAssist Pro.

        Args:
            scans: List of (image_path, scan_date) tuples
            clinical_context: Clinical history
            nodule_location: Optional specific nodule to track

        Returns:
            PipelineResult with longitudinal analysis
        """
        import time
        start_time = time.time()

        warnings = []
        errors = []

        # Sort scans by date
        scans_sorted = sorted(scans, key=lambda x: x[1])

        # Detect nodules in each scan
        detection_results = []
        for image_path, scan_date in scans_sorted:
            result = self.detector.detect(
                image_path,
                scan_date=scan_date,
                clinical_context=clinical_context
            )
            detection_results.append(result)

        # Extract measurements for longitudinal analysis
        measurements = self._extract_measurements_for_tracking(
            detection_results,
            nodule_location
        )

        # Check if we have enough data
        if len(measurements) < 2:
            warnings.append(
                "Insufficient nodule data for longitudinal analysis. "
                f"Found {len(measurements)} trackable measurements, need at least 2."
            )
            processing_time = (time.time() - start_time) * 1000
            return PipelineResult(
                detection_results=detection_results,
                nodule_count=sum(r.nodule_count for r in detection_results),
                scans_processed=len(detection_results),
                processing_time_ms=processing_time,
                warnings=warnings,
                errors=errors
            )

        # Run longitudinal analysis
        longitudinal_report = create_longitudinal_report(
            measurements,
            clinical_context or ""
        )

        # Generate differential evolution
        differentials = generate_differential_evolution(longitudinal_report.analysis)

        processing_time = (time.time() - start_time) * 1000

        return PipelineResult(
            detection_results=detection_results,
            longitudinal_report=longitudinal_report,
            differentials=differentials,
            nodule_count=len(measurements),
            scans_processed=len(detection_results),
            processing_time_ms=processing_time,
            warnings=warnings,
            errors=errors
        )

    def analyze_with_manual_measurements(
        self,
        measurements: List[Dict[str, Any]],
        clinical_context: Optional[str] = None
    ) -> PipelineResult:
        """
        Run longitudinal analysis with manually entered measurements.

        This is useful when nodule measurements are already known
        (e.g., from prior reports or manual measurement).

        Args:
            measurements: List of dicts with 'date', 'size_mm', 'location'
            clinical_context: Clinical history

        Returns:
            PipelineResult with longitudinal analysis
        """
        import time
        start_time = time.time()

        # Convert to NoduleMeasurement objects
        nodule_measurements = []
        for m in measurements:
            date = m.get('date')
            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            nodule_measurements.append(NoduleMeasurement(
                date=date,
                size_mm=m.get('size_mm', 0),
                location=m.get('location', 'unknown'),
                nodule_type=m.get('nodule_type', 'solid')
            ))

        # Sort by date
        nodule_measurements.sort(key=lambda x: x.date)

        # Run analysis
        longitudinal_report = create_longitudinal_report(
            nodule_measurements,
            clinical_context or ""
        )

        differentials = generate_differential_evolution(longitudinal_report.analysis)

        processing_time = (time.time() - start_time) * 1000

        return PipelineResult(
            detection_results=[],
            longitudinal_report=longitudinal_report,
            differentials=differentials,
            nodule_count=len(nodule_measurements),
            scans_processed=len(nodule_measurements),
            processing_time_ms=processing_time,
            warnings=[],
            errors=[]
        )

    def _extract_measurements_for_tracking(
        self,
        detection_results: List[DetectionResult],
        target_location: Optional[str] = None
    ) -> List[NoduleMeasurement]:
        """
        Extract nodule measurements for longitudinal tracking.

        Matches nodules across scans by location.
        """
        measurements = []

        for detection in detection_results:
            if not detection.has_nodules:
                continue

            # Find nodule to track
            if target_location:
                # Look for specific location
                matching_nodules = [
                    n for n in detection.nodules
                    if target_location.lower() in n.location.lower()
                ]
                if matching_nodules:
                    nodule = max(matching_nodules, key=lambda n: n.size_mm)
                else:
                    continue
            else:
                # Track largest nodule
                nodule = detection.get_largest_nodule()

            if nodule and nodule.size_mm >= self.config.min_nodule_size_mm:
                measurements.append(NoduleMeasurement(
                    date=detection.scan_metadata.scan_date,
                    size_mm=nodule.size_mm,
                    location=nodule.location,
                    nodule_type=nodule.nodule_type,
                    volume_mm3=nodule.volume_mm3,
                    morphology=nodule.morphology
                ))

        return measurements

    def generate_summary(self, result: PipelineResult) -> Dict[str, Any]:
        """
        Generate a human-readable summary of the analysis.

        Args:
            result: PipelineResult from analysis

        Returns:
            Dictionary with summary information
        """
        summary = {
            "scans_analyzed": result.scans_processed,
            "nodules_found": result.nodule_count,
            "has_longitudinal_data": result.has_longitudinal,
            "requires_action": result.requires_action,
        }

        if result.has_longitudinal:
            analysis = result.longitudinal_report.analysis
            summary.update({
                "risk_level": analysis.risk_level.value,
                "trajectory": analysis.trajectory.value,
                "size_change_percent": f"{analysis.size_change_percent:.1f}%",
                "volume_doubling_time": (
                    f"{analysis.volume_doubling_time_days:.0f} days"
                    if analysis.volume_doubling_time_days else "N/A"
                ),
                "lung_rads": (
                    analysis.lung_rads_current.value
                    if analysis.lung_rads_current else "N/A"
                ),
                "recommendations": analysis.recommendations,
                "clinical_interpretation": analysis.clinical_interpretation,
            })

        if result.warnings:
            summary["warnings"] = result.warnings

        return summary


def demo_pipeline():
    """Demo the full analysis pipeline."""
    print("=" * 70)
    print("RadAssist Pro - Image Analysis Pipeline Demo")
    print("\"AI That Remembers\"")
    print("=" * 70)
    print()

    # Create pipeline
    pipeline = ImageAnalysisPipeline()

    # Demo with manual measurements (simulating detected nodules)
    measurements = [
        {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "right upper lobe"},
        {"date": datetime(2024, 7, 20), "size_mm": 6.2, "location": "right upper lobe"},
        {"date": datetime(2025, 1, 18), "size_mm": 6.8, "location": "right upper lobe"},
        {"date": datetime(2025, 7, 15), "size_mm": 8.3, "location": "right upper lobe"},
    ]

    result = pipeline.analyze_with_manual_measurements(
        measurements,
        clinical_context="58-year-old female, former smoker (30 pack-years)"
    )

    # Print summary
    summary = pipeline.generate_summary(result)

    print("ANALYSIS SUMMARY")
    print("-" * 40)
    print(f"Scans Analyzed: {summary['scans_analyzed']}")
    print(f"Risk Level: {summary.get('risk_level', 'N/A').upper()}")
    print(f"Trajectory: {summary.get('trajectory', 'N/A')}")
    print(f"Size Change: {summary.get('size_change_percent', 'N/A')}")
    print(f"VDT: {summary.get('volume_doubling_time', 'N/A')}")
    print(f"Lung-RADS: Category {summary.get('lung_rads', 'N/A')}")
    print()

    print("RECOMMENDATIONS:")
    for i, rec in enumerate(summary.get('recommendations', []), 1):
        print(f"  {i}. {rec}")
    print()

    print("CLINICAL INTERPRETATION:")
    print(f"  {summary.get('clinical_interpretation', 'N/A')}")
    print()

    if result.requires_action:
        print("⚠️  THIS CASE REQUIRES CLINICAL ACTION")
    print()

    print("=" * 70)
    print("⚠️  DISCLAIMER: Demo only. Not for clinical use.")
    print("=" * 70)


if __name__ == "__main__":
    demo_pipeline()
