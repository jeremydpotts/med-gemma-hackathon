"""
Tests for longitudinal test case loader and comparison utilities.

Tests the LongitudinalTestCaseLoader and related functions for
RadAssist Pro's longitudinal comparison capabilities.
"""

import pytest
from pathlib import Path
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.longitudinal_loader import (
    LongitudinalTestCaseLoader,
    LongitudinalSeries,
    Timepoint,
    ExpectedChange,
    TestScenario,
    load_longitudinal_cases,
    create_comparison_prompt,
    validate_comparison_result
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def loader():
    """Create and load a test case loader."""
    loader = LongitudinalTestCaseLoader()
    loader.load()
    return loader


@pytest.fixture
def sample_series(loader):
    """Get a sample series for testing."""
    return loader.get_series("LONG_001")


# =============================================================================
# Loader Tests
# =============================================================================

class TestLongitudinalTestCaseLoader:
    """Tests for LongitudinalTestCaseLoader class."""

    def test_loader_initialization(self):
        """Test loader initializes correctly."""
        loader = LongitudinalTestCaseLoader()
        assert loader.data_path is not None
        assert loader._data is None
        assert len(loader._series) == 0

    def test_loader_load_success(self, loader):
        """Test loader successfully loads data."""
        assert len(loader._series) > 0
        assert len(loader._scenarios) > 0

    def test_loader_get_all_series(self, loader):
        """Test getting all series."""
        series_list = loader.get_all_series()
        assert len(series_list) >= 5  # We created 5 series
        assert all(isinstance(s, LongitudinalSeries) for s in series_list)

    def test_loader_get_series_by_id(self, loader):
        """Test getting series by ID."""
        series = loader.get_series("LONG_001")
        assert series is not None
        assert series.series_id == "LONG_001"
        assert series.case_name == "Pneumonia Resolution"

    def test_loader_get_nonexistent_series(self, loader):
        """Test getting non-existent series returns None."""
        series = loader.get_series("NONEXISTENT")
        assert series is None

    def test_loader_get_test_scenarios(self, loader):
        """Test getting test scenarios."""
        scenarios = loader.get_test_scenarios()
        assert len(scenarios) >= 4  # We created 4 scenarios
        assert all(isinstance(s, TestScenario) for s in scenarios)

    def test_loader_get_series_by_outcome(self, loader):
        """Test filtering series by outcome."""
        improving = loader.get_series_by_outcome("improvement")
        stable = loader.get_series_by_outcome("stable")
        worsening = loader.get_series_by_outcome("worsening")

        assert len(improving) >= 1
        assert len(stable) >= 1
        assert len(worsening) >= 1
        assert all(s.expected_outcome == "improvement" for s in improving)

    def test_loader_get_series_by_study_type(self, loader):
        """Test filtering series by study type."""
        xray_series = loader.get_series_by_study_type("chest_xray")
        ct_series = loader.get_series_by_study_type("ct_chest")

        assert len(xray_series) >= 1
        assert len(ct_series) >= 1

    def test_loader_get_metadata(self, loader):
        """Test getting metadata."""
        metadata = loader.get_metadata()
        assert "description" in metadata
        assert "disclaimer" in metadata

    def test_loader_get_summary(self, loader):
        """Test getting summary statistics."""
        summary = loader.get_summary()
        assert summary["loaded"] is True
        assert summary["num_series"] >= 5
        assert summary["total_timepoints"] > 0
        assert "outcomes_distribution" in summary


# =============================================================================
# Series Tests
# =============================================================================

class TestLongitudinalSeries:
    """Tests for LongitudinalSeries data class."""

    def test_series_has_required_fields(self, sample_series):
        """Test series has all required fields."""
        assert sample_series.series_id is not None
        assert sample_series.case_name is not None
        assert sample_series.description is not None
        assert sample_series.clinical_context is not None
        assert sample_series.expected_outcome is not None
        assert len(sample_series.timepoints) > 0

    def test_series_get_timepoint(self, sample_series):
        """Test getting timepoint by ID."""
        tp = sample_series.get_timepoint("T0")
        assert tp is not None
        assert tp.timepoint_id == "T0"

    def test_series_get_nonexistent_timepoint(self, sample_series):
        """Test getting non-existent timepoint returns None."""
        tp = sample_series.get_timepoint("T99")
        assert tp is None

    def test_series_get_timepoint_pair(self, sample_series):
        """Test getting timepoint pair."""
        pair = sample_series.get_timepoint_pair("T0", "T1")
        assert pair is not None
        t0, t1 = pair
        assert t0.timepoint_id == "T0"
        assert t1.timepoint_id == "T1"

    def test_series_num_timepoints(self, sample_series):
        """Test num_timepoints property."""
        assert sample_series.num_timepoints >= 2

    def test_series_total_days(self, sample_series):
        """Test total_days property."""
        assert sample_series.total_days > 0

    def test_series_expected_changes(self, sample_series):
        """Test expected changes are present."""
        assert len(sample_series.expected_changes) > 0
        for change in sample_series.expected_changes:
            assert isinstance(change, ExpectedChange)
            assert change.change_type in ["improvement", "stable", "worsening"]


# =============================================================================
# Timepoint Tests
# =============================================================================

class TestTimepoint:
    """Tests for Timepoint data class."""

    def test_timepoint_fields(self, sample_series):
        """Test timepoint has all required fields."""
        tp = sample_series.timepoints[0]
        assert tp.timepoint_id is not None
        assert tp.date is not None
        assert tp.study_type is not None
        assert tp.clinical_note is not None
        assert len(tp.synthetic_findings) > 0
        assert tp.impression is not None

    def test_timepoint_date_obj(self, sample_series):
        """Test date_obj property."""
        tp = sample_series.timepoints[0]
        date_obj = tp.date_obj
        assert isinstance(date_obj, datetime)

    def test_timepoint_day_offset(self, sample_series):
        """Test day_offset is correct."""
        t0 = sample_series.get_timepoint("T0")
        assert t0.day_offset == 0
        t1 = sample_series.get_timepoint("T1")
        assert t1.day_offset > 0


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_load_longitudinal_cases(self):
        """Test convenience load function."""
        loader = load_longitudinal_cases()
        assert len(loader.get_all_series()) > 0

    def test_create_comparison_prompt(self, sample_series):
        """Test comparison prompt generation."""
        prompt = create_comparison_prompt(sample_series, "T0", "T1")
        assert len(prompt) > 0
        assert "Clinical Context" in prompt
        assert "STUDY 1" in prompt
        assert "STUDY 2" in prompt
        assert "interval changes" in prompt.lower()

    def test_create_comparison_prompt_invalid_ids(self, sample_series):
        """Test prompt generation with invalid IDs returns empty."""
        prompt = create_comparison_prompt(sample_series, "T0", "T99")
        assert prompt == ""

    def test_validate_comparison_result_correct(self, sample_series):
        """Test validation with correct detection."""
        result = validate_comparison_result(
            sample_series, "T0", "T1", "improvement"
        )
        assert result["valid"] is True
        assert result["correct"] is True

    def test_validate_comparison_result_incorrect(self, sample_series):
        """Test validation with incorrect detection."""
        result = validate_comparison_result(
            sample_series, "T0", "T1", "worsening"
        )
        assert result["valid"] is True
        assert result["correct"] is False

    def test_validate_comparison_result_invalid_pair(self, sample_series):
        """Test validation with invalid timepoint pair."""
        result = validate_comparison_result(
            sample_series, "T0", "T99", "improvement"
        )
        assert result["valid"] is False
        assert "error" in result


# =============================================================================
# Specific Series Tests
# =============================================================================

class TestSpecificSeries:
    """Tests for specific longitudinal series."""

    def test_pneumonia_resolution_series(self, loader):
        """Test pneumonia resolution series (LONG_001)."""
        series = loader.get_series("LONG_001")
        assert series.case_name == "Pneumonia Resolution"
        assert series.expected_outcome == "improvement"
        assert series.num_timepoints == 3

        # Check findings progression
        t0 = series.get_timepoint("T0")
        t2 = series.get_timepoint("T2")
        assert "consolidation" in str(t0.synthetic_findings).lower()
        assert "resolution" in str(t2.synthetic_findings).lower()

    def test_nodule_surveillance_series(self, loader):
        """Test nodule surveillance series (LONG_002)."""
        series = loader.get_series("LONG_002")
        assert series.expected_outcome == "stable"

        # Check measurements exist
        t0 = series.get_timepoint("T0")
        assert "nodule_size_mm" in t0.measurements

    def test_heart_failure_series(self, loader):
        """Test heart failure series (LONG_003)."""
        series = loader.get_series("LONG_003")
        assert series.expected_outcome == "worsening"

        # Series has worsening then improving trajectory
        changes = series.expected_changes
        assert any(c.change_type == "worsening" for c in changes)
        assert any(c.change_type == "improvement" for c in changes)

    def test_nodule_growth_series(self, loader):
        """Test nodule growth series (LONG_005)."""
        series = loader.get_series("LONG_005")
        assert series.expected_outcome == "worsening"

        # Check measurements show growth
        t0 = series.get_timepoint("T0")
        t2 = series.get_timepoint("T2")
        assert t0.measurements["nodule_size_mm"] < t2.measurements["nodule_size_mm"]


# =============================================================================
# Test Scenario Tests
# =============================================================================

class TestTestScenarios:
    """Tests for test scenarios."""

    def test_improvement_scenario(self, loader):
        """Test improvement detection scenario."""
        scenarios = loader.get_test_scenarios()
        improvement_scenario = next(
            (s for s in scenarios if s.scenario_id == "TEST_IMPROVEMENT"),
            None
        )
        assert improvement_scenario is not None
        assert len(improvement_scenario.series_to_use) > 0

    def test_stability_scenario(self, loader):
        """Test stability detection scenario."""
        scenarios = loader.get_test_scenarios()
        stability_scenario = next(
            (s for s in scenarios if s.scenario_id == "TEST_STABILITY"),
            None
        )
        assert stability_scenario is not None

    def test_worsening_scenario(self, loader):
        """Test worsening detection scenario."""
        scenarios = loader.get_test_scenarios()
        worsening_scenario = next(
            (s for s in scenarios if s.scenario_id == "TEST_WORSENING"),
            None
        )
        assert worsening_scenario is not None

    def test_mixed_scenario(self, loader):
        """Test mixed trajectory scenario."""
        scenarios = loader.get_test_scenarios()
        mixed_scenario = next(
            (s for s in scenarios if s.scenario_id == "TEST_MIXED"),
            None
        )
        assert mixed_scenario is not None


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_workflow(self, loader):
        """Test full workflow from loading to validation."""
        # Load data
        assert loader.get_summary()["loaded"] is True

        # Get a series
        series = loader.get_series("LONG_001")
        assert series is not None

        # Create comparison prompt
        prompt = create_comparison_prompt(series, "T0", "T1")
        assert len(prompt) > 100

        # Simulate model detection (correct)
        detected = "improvement"
        result = validate_comparison_result(series, "T0", "T1", detected)
        assert result["correct"] is True

    def test_scenario_execution(self, loader):
        """Test executing a test scenario."""
        scenario = loader.get_test_scenarios()[0]

        for series_id in scenario.series_to_use:
            series = loader.get_series(series_id)
            assert series is not None

            # Verify we can create prompts for all timepoint pairs
            for i in range(len(series.timepoints) - 1):
                from_id = series.timepoints[i].timepoint_id
                to_id = series.timepoints[i + 1].timepoint_id
                prompt = create_comparison_prompt(series, from_id, to_id)
                assert len(prompt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
