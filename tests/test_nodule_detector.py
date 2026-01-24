"""
Tests for the nodule detector module.
"""

import pytest
from datetime import datetime
from src.core.nodule_detector import (
    NoduleDetector,
    DetectedNodule,
    DetectionResult,
    ScanMetadata,
    NoduleType,
    NoduleLocation
)


class TestDetectedNodule:
    """Test DetectedNodule dataclass."""

    def test_create_nodule(self):
        """Test creating a detected nodule."""
        nodule = DetectedNodule(
            nodule_id="nodule_1",
            location="right upper lobe",
            nodule_type="solid",
            size_mm=8.0,
            confidence=0.87
        )
        assert nodule.nodule_id == "nodule_1"
        assert nodule.size_mm == 8.0
        assert nodule.confidence == 0.87

    def test_nodule_to_dict(self):
        """Test converting nodule to dictionary."""
        nodule = DetectedNodule(
            nodule_id="nodule_1",
            location="RUL",
            size_mm=6.0
        )
        d = nodule.to_dict()
        assert d["nodule_id"] == "nodule_1"
        assert d["size_mm"] == 6.0


class TestScanMetadata:
    """Test ScanMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating scan metadata."""
        meta = ScanMetadata(
            scan_date=datetime(2024, 1, 15),
            modality="CT"
        )
        assert meta.scan_date == datetime(2024, 1, 15)
        assert meta.modality == "CT"

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        meta = ScanMetadata(
            scan_date=datetime(2024, 1, 15),
            modality="CT",
            slice_thickness_mm=1.25
        )
        d = meta.to_dict()
        assert "2024-01-15" in d["scan_date"]
        assert d["modality"] == "CT"


class TestDetectionResult:
    """Test DetectionResult dataclass."""

    def test_nodule_count(self):
        """Test nodule counting."""
        result = DetectionResult(
            scan_metadata=ScanMetadata(scan_date=datetime.now()),
            nodules=[
                DetectedNodule("n1", "RUL", size_mm=6.0),
                DetectedNodule("n2", "LLL", size_mm=4.0),
            ]
        )
        assert result.nodule_count == 2
        assert result.has_nodules is True

    def test_no_nodules(self):
        """Test result with no nodules."""
        result = DetectionResult(
            scan_metadata=ScanMetadata(scan_date=datetime.now()),
            nodules=[]
        )
        assert result.nodule_count == 0
        assert result.has_nodules is False

    def test_get_largest_nodule(self):
        """Test getting largest nodule."""
        result = DetectionResult(
            scan_metadata=ScanMetadata(scan_date=datetime.now()),
            nodules=[
                DetectedNodule("n1", "RUL", size_mm=6.0),
                DetectedNodule("n2", "LLL", size_mm=12.0),
                DetectedNodule("n3", "RML", size_mm=4.0),
            ]
        )
        largest = result.get_largest_nodule()
        assert largest.nodule_id == "n2"
        assert largest.size_mm == 12.0

    def test_get_largest_nodule_empty(self):
        """Test getting largest nodule when empty."""
        result = DetectionResult(
            scan_metadata=ScanMetadata(scan_date=datetime.now()),
            nodules=[]
        )
        assert result.get_largest_nodule() is None


class TestNoduleDetector:
    """Test NoduleDetector class."""

    def test_init_mock_mode(self):
        """Test initializing in mock mode."""
        detector = NoduleDetector()
        assert detector._mock_mode is True

    def test_detect_returns_result(self):
        """Test detection returns a result."""
        detector = NoduleDetector()
        result = detector.detect(
            "/path/to/scan.dcm",
            scan_date=datetime(2024, 1, 15)
        )
        assert isinstance(result, DetectionResult)
        assert result.scan_metadata.scan_date == datetime(2024, 1, 15)

    def test_detect_with_clinical_context(self):
        """Test detection with clinical context."""
        detector = NoduleDetector()
        result = detector.detect(
            "/path/to/scan.dcm",
            clinical_context="Former smoker with cough"
        )
        assert result is not None

    def test_mock_detection_returns_nodule(self):
        """Test mock detection returns a nodule."""
        detector = NoduleDetector()
        result = detector.detect("/path/to/scan.dcm")
        assert result.has_nodules is True
        assert result.nodule_count >= 1

    def test_detect_batch(self):
        """Test batch detection."""
        detector = NoduleDetector()
        results = detector.detect_batch(
            ["/scan1.dcm", "/scan2.dcm"],
            scan_dates=[datetime(2024, 1, 15), datetime(2024, 7, 15)]
        )
        assert len(results) == 2


class TestLocationNormalization:
    """Test location normalization."""

    def test_normalize_rul(self):
        """Test normalizing RUL."""
        detector = NoduleDetector()
        assert detector._normalize_location("RUL") == "right upper lobe"
        assert detector._normalize_location("rul") == "right upper lobe"

    def test_normalize_full_name(self):
        """Test normalizing full name."""
        detector = NoduleDetector()
        assert detector._normalize_location("right upper lobe") == "right upper lobe"
        assert detector._normalize_location("Right Upper") == "right upper lobe"

    def test_normalize_unknown(self):
        """Test normalizing unknown location."""
        detector = NoduleDetector()
        result = detector._normalize_location("mediastinum")
        assert result == "mediastinum"  # Returns as-is


class TestNoduleTypes:
    """Test nodule type enumeration."""

    def test_nodule_types_exist(self):
        """Test nodule types are defined."""
        assert NoduleType.SOLID.value == "solid"
        assert NoduleType.PART_SOLID.value == "part-solid"
        assert NoduleType.GROUND_GLASS.value == "ground-glass"

    def test_nodule_locations_exist(self):
        """Test nodule locations are defined."""
        assert NoduleLocation.RIGHT_UPPER_LOBE.value == "right upper lobe"
        assert NoduleLocation.LEFT_LOWER_LOBE.value == "left lower lobe"
