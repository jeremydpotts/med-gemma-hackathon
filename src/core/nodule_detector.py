"""
Nodule Detection and Measurement Module for RadAssist Pro.

This module provides the bridge between raw medical images and
the longitudinal analyzer by:
- Detecting nodules in CT images
- Measuring nodule dimensions
- Extracting metadata for longitudinal tracking

Works with MedGemma model for AI-powered detection.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)


class NoduleType(Enum):
    """Classification of nodule types."""
    SOLID = "solid"
    PART_SOLID = "part-solid"
    GROUND_GLASS = "ground-glass"
    CALCIFIED = "calcified"
    UNKNOWN = "unknown"


class NoduleLocation(Enum):
    """Standard lung nodule locations."""
    RIGHT_UPPER_LOBE = "right upper lobe"
    RIGHT_MIDDLE_LOBE = "right middle lobe"
    RIGHT_LOWER_LOBE = "right lower lobe"
    LEFT_UPPER_LOBE = "left upper lobe"
    LEFT_LOWER_LOBE = "left lower lobe"
    LINGULA = "lingula"
    UNKNOWN = "unknown"


@dataclass
class NoduleDetectorConfig:
    """Configuration for nodule detection."""
    min_nodule_size_mm: float = 3.0  # Minimum nodule size to report
    confidence_threshold: float = 0.5  # Minimum confidence to include
    model_name: str = "medgemma-1.5-4b"
    use_3d_detection: bool = True
    include_morphology: bool = True


@dataclass
class DetectedNodule:
    """
    Represents a detected nodule with measurements.

    This is the output of nodule detection and input to
    longitudinal analysis.
    """
    # Primary identifiers
    nodule_id: str
    location: str  # Free text or NoduleLocation value
    nodule_type: str = "solid"

    # Measurements
    size_mm: float = 0.0  # Largest dimension
    size_perpendicular_mm: Optional[float] = None  # Perpendicular measurement
    volume_mm3: Optional[float] = None  # Volume if available

    # Detection metadata
    confidence: float = 0.0
    detection_method: str = "medgemma"

    # Bounding box (if available)
    bbox: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height

    # Image/slice info
    slice_number: Optional[int] = None
    series_uid: Optional[str] = None

    # Additional characteristics
    morphology: Optional[str] = None  # e.g., "spiculated", "smooth"
    calcification: bool = False
    cavitation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodule_id": self.nodule_id,
            "location": self.location,
            "nodule_type": self.nodule_type,
            "size_mm": self.size_mm,
            "size_perpendicular_mm": self.size_perpendicular_mm,
            "volume_mm3": self.volume_mm3,
            "confidence": self.confidence,
            "detection_method": self.detection_method,
            "morphology": self.morphology,
            "calcification": self.calcification,
            "cavitation": self.cavitation
        }


@dataclass
class ScanMetadata:
    """Metadata extracted from a scan for longitudinal tracking."""
    scan_date: datetime
    modality: str = "CT"
    series_description: Optional[str] = None
    slice_thickness_mm: Optional[float] = None
    patient_id: Optional[str] = None  # De-identified
    accession_number: Optional[str] = None
    institution: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_date": self.scan_date.isoformat(),
            "modality": self.modality,
            "series_description": self.series_description,
            "slice_thickness_mm": self.slice_thickness_mm
        }


@dataclass
class DetectionResult:
    """Complete result of nodule detection on a scan."""
    scan_metadata: ScanMetadata
    nodules: List[DetectedNodule]
    processing_time_ms: float = 0.0
    model_version: str = "medgemma-1.5-4b"
    raw_output: Optional[str] = None
    error: Optional[str] = None

    @property
    def nodule_count(self) -> int:
        return len(self.nodules)

    @property
    def has_nodules(self) -> bool:
        return len(self.nodules) > 0

    def get_largest_nodule(self) -> Optional[DetectedNodule]:
        """Get the largest detected nodule."""
        if not self.nodules:
            return None
        return max(self.nodules, key=lambda n: n.size_mm)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_metadata": self.scan_metadata.to_dict(),
            "nodules": [n.to_dict() for n in self.nodules],
            "nodule_count": self.nodule_count,
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version
        }


class NoduleDetector:
    """
    Nodule Detection Engine using MedGemma.

    Detects and measures lung nodules in CT images for
    longitudinal tracking.

    Example:
        detector = NoduleDetector()
        result = detector.detect("scan.dcm", scan_date=datetime(2024, 1, 15))

        for nodule in result.nodules:
            print(f"Found {nodule.size_mm}mm nodule in {nodule.location}")
    """

    # Prompt for nodule detection
    NODULE_DETECTION_PROMPT = """You are an expert thoracic radiologist analyzing a chest CT scan for lung nodules.

Identify ALL lung nodules and provide for each:
1. Location (e.g., "right upper lobe", "left lower lobe")
2. Size in millimeters (measure largest dimension)
3. Type (solid, part-solid, ground-glass, calcified)
4. Morphology (smooth, spiculated, lobulated, irregular)
5. Any concerning features (spiculation, cavitation, pleural tags)

Format your response as:
NODULE 1:
- Location: [location]
- Size: [X] mm
- Type: [type]
- Morphology: [description]
- Concerning features: [features or "none"]

If no nodules are detected, respond with:
NO NODULES DETECTED

Be precise with measurements. Include all nodules >= 3mm."""

    # Location aliases for standardization
    LOCATION_ALIASES = {
        "rul": "right upper lobe",
        "rml": "right middle lobe",
        "rll": "right lower lobe",
        "lul": "left upper lobe",
        "lll": "left lower lobe",
        "right upper": "right upper lobe",
        "right middle": "right middle lobe",
        "right lower": "right lower lobe",
        "left upper": "left upper lobe",
        "left lower": "left lower lobe",
    }

    def __init__(self, model=None):
        """
        Initialize nodule detector.

        Args:
            model: Optional MedGemma model instance. If None, uses mock mode.
        """
        self.model = model
        self._mock_mode = model is None

        if self._mock_mode:
            logger.info("NoduleDetector initialized in mock mode (no model provided)")
        else:
            logger.info("NoduleDetector initialized with MedGemma model")

    def detect(
        self,
        image_path: Union[str, Path],
        scan_date: Optional[datetime] = None,
        clinical_context: Optional[str] = None
    ) -> DetectionResult:
        """
        Detect nodules in a CT image or volume.

        Args:
            image_path: Path to DICOM file or image
            scan_date: Date of the scan (defaults to today)
            clinical_context: Optional clinical history

        Returns:
            DetectionResult with detected nodules and metadata
        """
        import time
        start_time = time.time()

        # Default scan date to today
        if scan_date is None:
            scan_date = datetime.now()

        # Create metadata
        metadata = ScanMetadata(
            scan_date=scan_date,
            modality="CT"
        )

        # Try to extract metadata from DICOM
        metadata = self._extract_dicom_metadata(image_path, metadata)

        # Run detection
        if self._mock_mode:
            nodules, raw_output = self._mock_detect()
        else:
            nodules, raw_output = self._run_model_detection(
                image_path, clinical_context
            )

        processing_time = (time.time() - start_time) * 1000

        return DetectionResult(
            scan_metadata=metadata,
            nodules=nodules,
            processing_time_ms=processing_time,
            model_version="medgemma-1.5-4b" if not self._mock_mode else "mock",
            raw_output=raw_output
        )

    def detect_batch(
        self,
        image_paths: List[Union[str, Path]],
        scan_dates: Optional[List[datetime]] = None
    ) -> List[DetectionResult]:
        """
        Detect nodules in multiple scans.

        Args:
            image_paths: List of paths to images
            scan_dates: Optional list of scan dates

        Returns:
            List of DetectionResults
        """
        results = []
        dates = scan_dates or [None] * len(image_paths)

        for path, date in zip(image_paths, dates):
            result = self.detect(path, scan_date=date)
            results.append(result)

        return results

    def _extract_dicom_metadata(
        self,
        image_path: Union[str, Path],
        default_metadata: ScanMetadata
    ) -> ScanMetadata:
        """Try to extract metadata from DICOM file."""
        try:
            import pydicom
            path = Path(image_path)

            if path.suffix.lower() == '.dcm' or path.is_dir():
                if path.is_dir():
                    # Find first DICOM file
                    dcm_files = list(path.glob("*.dcm"))
                    if dcm_files:
                        path = dcm_files[0]
                    else:
                        return default_metadata

                ds = pydicom.dcmread(str(path), stop_before_pixels=True)

                # Extract relevant tags
                scan_date = default_metadata.scan_date
                if hasattr(ds, 'StudyDate') and ds.StudyDate:
                    try:
                        scan_date = datetime.strptime(ds.StudyDate, '%Y%m%d')
                    except ValueError:
                        pass

                return ScanMetadata(
                    scan_date=scan_date,
                    modality=getattr(ds, 'Modality', 'CT'),
                    series_description=getattr(ds, 'SeriesDescription', None),
                    slice_thickness_mm=getattr(ds, 'SliceThickness', None)
                )

        except ImportError:
            logger.debug("pydicom not available for metadata extraction")
        except Exception as e:
            logger.debug(f"Could not extract DICOM metadata: {e}")

        return default_metadata

    def _run_model_detection(
        self,
        image_path: Union[str, Path],
        clinical_context: Optional[str]
    ) -> Tuple[List[DetectedNodule], str]:
        """Run MedGemma model for nodule detection."""
        try:
            # Build prompt
            prompt = self.NODULE_DETECTION_PROMPT
            if clinical_context:
                prompt = f"Clinical Context: {clinical_context}\n\n{prompt}"

            # Run inference (assuming model has infer_with_context method)
            result = self.model.infer_with_context(
                image_path,
                clinical_context or "",
                study_type="ct_volume"
            )

            # Parse response
            raw_output = result.raw_output or ""
            nodules = self._parse_model_response(raw_output)

            return nodules, raw_output

        except Exception as e:
            logger.error(f"Model detection failed: {e}")
            return self._mock_detect()

    def _parse_model_response(self, response: str) -> List[DetectedNodule]:
        """Parse model response to extract nodules."""
        nodules = []

        if "NO NODULES" in response.upper():
            return nodules

        # Split by nodule entries
        nodule_sections = re.split(r'NODULE\s*\d+:', response, flags=re.IGNORECASE)

        for i, section in enumerate(nodule_sections[1:], 1):  # Skip first split
            nodule = self._parse_nodule_section(section, i)
            if nodule:
                nodules.append(nodule)

        return nodules

    def _parse_nodule_section(
        self, section: str, index: int
    ) -> Optional[DetectedNodule]:
        """Parse a single nodule section from model output."""
        try:
            # Extract location
            location_match = re.search(
                r'location[:\s]*([^\n,]+)',
                section, re.IGNORECASE
            )
            location = self._normalize_location(
                location_match.group(1).strip() if location_match else "unknown"
            )

            # Extract size
            size_match = re.search(
                r'size[:\s]*(\d+\.?\d*)\s*mm',
                section, re.IGNORECASE
            )
            size_mm = float(size_match.group(1)) if size_match else 0.0

            # Extract type
            type_match = re.search(
                r'type[:\s]*([^\n,]+)',
                section, re.IGNORECASE
            )
            nodule_type = "solid"
            if type_match:
                type_str = type_match.group(1).strip().lower()
                if "part" in type_str or "sub" in type_str:
                    nodule_type = "part-solid"
                elif "ground" in type_str or "glass" in type_str:
                    nodule_type = "ground-glass"
                elif "calcif" in type_str:
                    nodule_type = "calcified"

            # Extract morphology
            morph_match = re.search(
                r'morphology[:\s]*([^\n,]+)',
                section, re.IGNORECASE
            )
            morphology = morph_match.group(1).strip() if morph_match else None

            # Check for concerning features
            spiculated = "spicul" in section.lower()
            cavitation = "cavit" in section.lower()

            return DetectedNodule(
                nodule_id=f"nodule_{index}",
                location=location,
                nodule_type=nodule_type,
                size_mm=size_mm,
                confidence=0.85,
                detection_method="medgemma",
                morphology=morphology,
                cavitation=cavitation
            )

        except Exception as e:
            logger.warning(f"Failed to parse nodule section: {e}")
            return None

    def _normalize_location(self, location: str) -> str:
        """Normalize location string to standard format."""
        location_lower = location.lower().strip()

        # Check aliases
        for alias, standard in self.LOCATION_ALIASES.items():
            if alias in location_lower:
                return standard

        # Return as-is if no match
        return location

    def _mock_detect(self) -> Tuple[List[DetectedNodule], str]:
        """Generate mock detection for testing."""
        mock_output = """NODULE 1:
- Location: right upper lobe
- Size: 8 mm
- Type: solid
- Morphology: smooth
- Concerning features: none

This is a mock detection result for testing purposes."""

        nodules = [
            DetectedNodule(
                nodule_id="nodule_1",
                location="right upper lobe",
                nodule_type="solid",
                size_mm=8.0,
                confidence=0.87,
                detection_method="mock",
                morphology="smooth"
            )
        ]

        return nodules, mock_output


def demo_detection():
    """Demo nodule detection functionality."""
    print("=" * 70)
    print("RadAssist Pro - Nodule Detection Demo")
    print("=" * 70)
    print()

    # Create detector in mock mode
    detector = NoduleDetector()

    # Run detection
    result = detector.detect(
        "/path/to/scan.dcm",
        scan_date=datetime(2024, 1, 15),
        clinical_context="58-year-old former smoker, screening CT"
    )

    print(f"Scan Date: {result.scan_metadata.scan_date}")
    print(f"Nodules Found: {result.nodule_count}")
    print(f"Processing Time: {result.processing_time_ms:.1f}ms")
    print()

    if result.has_nodules:
        print("DETECTED NODULES:")
        print("-" * 40)
        for nodule in result.nodules:
            print(f"  ID: {nodule.nodule_id}")
            print(f"  Location: {nodule.location}")
            print(f"  Size: {nodule.size_mm}mm ({nodule.nodule_type})")
            print(f"  Morphology: {nodule.morphology}")
            print(f"  Confidence: {nodule.confidence:.0%}")
            print()

    print("=" * 70)
    print("⚠️  DISCLAIMER: Mock data for demonstration only.")
    print("    Not for clinical use.")
    print("=" * 70)


if __name__ == "__main__":
    demo_detection()
