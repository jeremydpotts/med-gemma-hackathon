"""
Tests for the image analysis pipeline.
"""

import pytest
from datetime import datetime
from src.core.image_analysis_pipeline import (
    ImageAnalysisPipeline,
    AnalysisPipelineConfig,
    PipelineResult
)
from src.core.longitudinal_analyzer import RiskLevel, ChangeTrajectory


class TestAnalysisPipelineConfig:
    """Test AnalysisPipelineConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = AnalysisPipelineConfig()
        assert config.min_nodule_size_mm == 3.0
        assert config.mock_mode is True


class TestImageAnalysisPipeline:
    """Test ImageAnalysisPipeline."""

    def test_init(self):
        """Test pipeline initialization."""
        pipeline = ImageAnalysisPipeline()
        assert pipeline is not None
        assert pipeline.config.mock_mode is True

    def test_analyze_single(self):
        """Test single scan analysis."""
        pipeline = ImageAnalysisPipeline()
        result = pipeline.analyze_single(
            "/path/to/scan.dcm",
            scan_date=datetime(2024, 1, 15)
        )
        assert isinstance(result, PipelineResult)
        assert result.scans_processed == 1

    def test_analyze_with_manual_measurements(self):
        """Test analysis with manual measurements."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)

        assert result.has_longitudinal is True
        assert result.longitudinal_report is not None

    def test_analyze_with_string_dates(self):
        """Test analysis with string dates."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": "2024-01-15", "size_mm": 6.0, "location": "RUL"},
            {"date": "2024-07-15", "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)
        assert result.has_longitudinal is True

    def test_growing_nodule_detection(self):
        """Test detection of growing nodule."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)

        assert result.longitudinal_report.analysis.trajectory == ChangeTrajectory.WORSENING
        assert result.longitudinal_report.analysis.size_change_mm > 0

    def test_stable_nodule_detection(self):
        """Test detection of stable nodule."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 6.1, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)

        assert result.longitudinal_report.analysis.trajectory == ChangeTrajectory.STABLE

    def test_clinical_context_preserved(self):
        """Test that clinical context is preserved."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        context = "58-year-old former smoker"
        result = pipeline.analyze_with_manual_measurements(measurements, context)

        assert result.longitudinal_report.patient_context == context


class TestPipelineResult:
    """Test PipelineResult."""

    def test_has_longitudinal_false(self):
        """Test has_longitudinal when no report."""
        result = PipelineResult(
            detection_results=[],
            longitudinal_report=None
        )
        assert result.has_longitudinal is False

    def test_requires_action_high_risk(self):
        """Test requires_action for high risk."""
        pipeline = ImageAnalysisPipeline()
        # Create high-risk scenario
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 8.0, "location": "RUL"},
            {"date": datetime(2024, 4, 15), "size_mm": 12.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)

        # Fast growth should be high risk
        assert result.requires_action is True

    def test_requires_action_low_risk(self):
        """Test requires_action for low risk."""
        pipeline = ImageAnalysisPipeline()
        # Create low-risk scenario
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 4.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 4.1, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)

        # Stable small nodule should not require action
        assert result.requires_action is False


class TestGenerateSummary:
    """Test summary generation."""

    def test_summary_includes_basics(self):
        """Test summary includes basic info."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)
        summary = pipeline.generate_summary(result)

        assert "scans_analyzed" in summary
        assert "nodules_found" in summary
        assert "has_longitudinal_data" in summary

    def test_summary_includes_longitudinal_details(self):
        """Test summary includes longitudinal details."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)
        summary = pipeline.generate_summary(result)

        assert "risk_level" in summary
        assert "trajectory" in summary
        assert "recommendations" in summary

    def test_summary_recommendations_not_empty(self):
        """Test summary has recommendations."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 15), "size_mm": 8.0, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(measurements)
        summary = pipeline.generate_summary(result)

        assert len(summary["recommendations"]) > 0


class TestMultipleTimepoints:
    """Test with multiple timepoints."""

    def test_four_timepoint_analysis(self):
        """Test analysis with 4 timepoints."""
        pipeline = ImageAnalysisPipeline()
        measurements = [
            {"date": datetime(2024, 1, 15), "size_mm": 6.0, "location": "RUL"},
            {"date": datetime(2024, 7, 20), "size_mm": 6.2, "location": "RUL"},
            {"date": datetime(2025, 1, 18), "size_mm": 6.8, "location": "RUL"},
            {"date": datetime(2025, 7, 15), "size_mm": 8.3, "location": "RUL"},
        ]
        result = pipeline.analyze_with_manual_measurements(
            measurements,
            clinical_context="58-year-old former smoker"
        )

        assert result.scans_processed == 4
        assert result.has_longitudinal is True
        assert len(result.longitudinal_report.measurements) == 4

    def test_demo_scenario_the_missed_progression(self):
        """Test 'The Missed Progression Save' demo scenario."""
        pipeline = ImageAnalysisPipeline()

        # This is the exact demo scenario from the storyboard
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

        analysis = result.longitudinal_report.analysis

        # Verify the key findings that "traditional reads missed"
        assert analysis.trajectory == ChangeTrajectory.WORSENING
        assert analysis.risk_level == RiskLevel.HIGH
        assert analysis.volume_doubling_time_days is not None
        assert analysis.volume_doubling_time_days < 400  # Concerning threshold
        assert analysis.lung_rads_current is not None
        assert "4" in analysis.lung_rads_current.value  # Should be 4B

        # Verify recommendations include further workup
        recs_text = " ".join(analysis.recommendations).lower()
        assert any(word in recs_text for word in ["pet", "tissue", "biopsy"])
