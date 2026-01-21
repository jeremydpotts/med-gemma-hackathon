"""
Pytest configuration and fixtures for Med-Gemma RadAssist Pro testing.

This module provides shared fixtures, test data, and configuration
for all test modules in the project.
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Configuration
# =============================================================================

TEST_DATA_DIR = Path(__file__).parent / "test_data"
SAMPLE_IMAGES_DIR = TEST_DATA_DIR / "images"
SAMPLE_DICOMS_DIR = TEST_DATA_DIR / "dicoms"
GROUND_TRUTH_FILE = TEST_DATA_DIR / "ground_truth_cases.json"


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return TEST_DATA_DIR


@pytest.fixture(scope="session")
def sample_images_dir() -> Path:
    """Return path to sample images directory."""
    return SAMPLE_IMAGES_DIR


@pytest.fixture
def sample_chest_xray_path(sample_images_dir) -> Path:
    """Return path to a sample chest X-ray image."""
    return sample_images_dir / "sample_chest_xray.png"


@pytest.fixture
def sample_ct_volume_path(test_data_dir) -> Path:
    """Return path to a sample CT volume directory."""
    return test_data_dir / "dicoms" / "sample_ct_volume"


@pytest.fixture
def ground_truth_cases() -> List[Dict[str, Any]]:
    """Load ground truth test cases for accuracy validation."""
    if GROUND_TRUTH_FILE.exists():
        with open(GROUND_TRUTH_FILE) as f:
            return json.load(f)
    # Return synthetic test cases if file doesn't exist
    return [
        {
            "case_id": "SYNTH_001",
            "image_type": "chest_xray",
            "expected_findings": ["normal"],
            "confidence_threshold": 0.7
        },
        {
            "case_id": "SYNTH_002",
            "image_type": "chest_xray",
            "expected_findings": ["cardiomegaly"],
            "confidence_threshold": 0.6
        },
        {
            "case_id": "SYNTH_003",
            "image_type": "chest_xray",
            "expected_findings": ["pneumonia", "consolidation"],
            "confidence_threshold": 0.5
        }
    ]


# =============================================================================
# Mock Model Fixtures
# =============================================================================

@pytest.fixture
def mock_medgemma_model():
    """Create a mock MedGemma model for testing without GPU."""
    mock = MagicMock()

    # Mock inference method
    mock.infer.return_value = {
        "findings": ["No acute cardiopulmonary abnormality"],
        "confidence": 0.85,
        "processing_time_ms": 150,
        "model_version": "medgemma-1.5-4b-mock"
    }

    # Mock 3D inference
    mock.infer_3d.return_value = {
        "findings": ["No significant abnormality detected in CT volume"],
        "measurements": {"lung_volume_ml": 5200},
        "confidence": 0.82,
        "processing_time_ms": 8500,
        "slices_processed": 256
    }

    # Mock longitudinal comparison
    mock.compare_longitudinal.return_value = {
        "comparison": "No significant interval change",
        "changes_detected": [],
        "confidence": 0.78,
        "timepoints_compared": 2
    }

    return mock


@pytest.fixture
def mock_medgemma_response_normal() -> Dict[str, Any]:
    """Return a mock normal chest X-ray response."""
    return {
        "findings": [
            "Heart size is normal",
            "Lungs are clear bilaterally",
            "No pleural effusion",
            "No pneumothorax",
            "Mediastinal contours are unremarkable"
        ],
        "impression": "No acute cardiopulmonary abnormality",
        "confidence": 0.89,
        "processing_time_ms": 145,
        "model_version": "medgemma-1.5-4b"
    }


@pytest.fixture
def mock_medgemma_response_abnormal() -> Dict[str, Any]:
    """Return a mock abnormal chest X-ray response."""
    return {
        "findings": [
            "Cardiomegaly present",
            "Bilateral pulmonary infiltrates",
            "Small left pleural effusion",
            "No pneumothorax"
        ],
        "impression": "Cardiomegaly with bilateral infiltrates, concerning for CHF",
        "confidence": 0.76,
        "abnormalities_detected": ["cardiomegaly", "infiltrates", "effusion"],
        "processing_time_ms": 162,
        "model_version": "medgemma-1.5-4b"
    }


# =============================================================================
# Synthetic Data Fixtures
# =============================================================================

@pytest.fixture
def synthetic_patient_data() -> Dict[str, Any]:
    """Generate synthetic patient data (no PHI)."""
    return {
        "patient_id": "SYNTH_PAT_001",  # Synthetic ID
        "age_range": "60-70",  # Age range, not exact age
        "sex": "M",
        "study_type": "chest_xray",
        "study_date": "2026-01-15",  # Synthetic date
        "clinical_history": "Routine screening examination",
        "is_synthetic": True  # Flag to indicate synthetic data
    }


@pytest.fixture
def synthetic_dicom_metadata() -> Dict[str, Any]:
    """Generate synthetic DICOM metadata (de-identified)."""
    return {
        "Modality": "CR",
        "BodyPartExamined": "CHEST",
        "ViewPosition": "PA",
        "Rows": 2048,
        "Columns": 2048,
        "BitsStored": 12,
        "PhotometricInterpretation": "MONOCHROME2",
        "PatientID": "ANONYMOUS",  # De-identified
        "PatientName": "ANONYMOUS",  # De-identified
        "PatientBirthDate": "",  # Removed
        "InstitutionName": "SYNTHETIC_HOSPITAL",
        "StudyDescription": "CHEST PA",
        "is_deidentified": True
    }


# =============================================================================
# Temporary File Fixtures
# =============================================================================

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_report_file(temp_output_dir) -> Path:
    """Create a temporary file for report output."""
    return temp_output_dir / "test_report.json"


# =============================================================================
# Security/HIPAA Fixtures
# =============================================================================

@pytest.fixture
def hipaa_identifiers() -> List[str]:
    """Return list of HIPAA identifiers to check for in data."""
    return [
        "name", "address", "date", "phone", "fax", "email",
        "ssn", "social_security", "mrn", "medical_record",
        "health_plan", "account", "license", "vehicle",
        "device_serial", "url", "ip_address", "biometric",
        "photo", "identifier"
    ]


@pytest.fixture
def mock_encryption_key() -> bytes:
    """Generate a mock encryption key for testing."""
    # DO NOT use in production - for testing only
    return b"test_key_for_unit_tests_only_32b"


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger for testing."""
    mock = MagicMock()
    mock.log_access.return_value = True
    mock.get_logs.return_value = []
    return mock


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Define performance thresholds for testing."""
    return {
        "2d_inference_max_ms": 10000,  # 10 seconds max for 2D
        "3d_inference_max_ms": 30000,  # 30 seconds max for 3D
        "preprocessing_max_ms": 5000,  # 5 seconds max for preprocessing
        "report_generation_max_ms": 2000,  # 2 seconds max for report gen
        "memory_max_gb": 16  # Max GPU memory usage
    }


# =============================================================================
# API/Integration Fixtures
# =============================================================================

@pytest.fixture
def mock_api_client():
    """Create a mock API client for integration testing."""
    mock = MagicMock()
    mock.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    mock.upload_image.return_value = {"image_id": "test_123", "status": "uploaded"}
    mock.get_results.return_value = {"status": "complete", "findings": []}
    return mock


# =============================================================================
# Session-scoped Setup
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before all tests."""
    # Create test data directories if they don't exist
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DICOMS_DIR.mkdir(parents=True, exist_ok=True)

    # Set environment variables for testing
    os.environ["RADASSIST_ENV"] = "testing"
    os.environ["RADASSIST_LOG_LEVEL"] = "DEBUG"

    yield

    # Cleanup after all tests
    os.environ.pop("RADASSIST_ENV", None)
    os.environ.pop("RADASSIST_LOG_LEVEL", None)


# =============================================================================
# Markers Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU"
    )
    config.addinivalue_line(
        "markers", "security: marks security-related tests"
    )
    config.addinivalue_line(
        "markers", "medical_accuracy: marks medical accuracy validation tests"
    )
