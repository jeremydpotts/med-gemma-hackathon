"""
Longitudinal Test Case Loader for RadAssist Pro.

Provides utilities for loading and working with longitudinal
test cases for testing MedGemma's temporal comparison capabilities.

This module is used for development and testing purposes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Timepoint:
    """Represents a single timepoint in a longitudinal series."""
    timepoint_id: str
    date: str
    day_offset: int
    study_type: str
    clinical_note: str
    synthetic_findings: List[str]
    impression: str
    measurements: Dict[str, Any] = field(default_factory=dict)

    @property
    def date_obj(self) -> datetime:
        """Get date as datetime object."""
        return datetime.strptime(self.date, "%Y-%m-%d")


@dataclass
class ExpectedChange:
    """Represents expected change between timepoints."""
    from_timepoint: str
    to_timepoint: str
    change_type: str  # improvement, stable, worsening
    findings: List[str]


@dataclass
class LongitudinalSeries:
    """Represents a complete longitudinal series of studies."""
    series_id: str
    case_name: str
    description: str
    clinical_context: str
    expected_outcome: str
    timepoints: List[Timepoint]
    expected_changes: List[ExpectedChange]

    def get_timepoint(self, timepoint_id: str) -> Optional[Timepoint]:
        """Get a specific timepoint by ID."""
        for tp in self.timepoints:
            if tp.timepoint_id == timepoint_id:
                return tp
        return None

    def get_timepoint_pair(
        self, from_id: str, to_id: str
    ) -> Optional[Tuple[Timepoint, Timepoint]]:
        """Get a pair of timepoints for comparison."""
        from_tp = self.get_timepoint(from_id)
        to_tp = self.get_timepoint(to_id)
        if from_tp and to_tp:
            return (from_tp, to_tp)
        return None

    @property
    def num_timepoints(self) -> int:
        """Number of timepoints in series."""
        return len(self.timepoints)

    @property
    def total_days(self) -> int:
        """Total days spanned by series."""
        if not self.timepoints:
            return 0
        return max(tp.day_offset for tp in self.timepoints)


@dataclass
class TestScenario:
    """Represents a test scenario for validation."""
    scenario_id: str
    description: str
    series_to_use: List[str]
    expected_result: str


# =============================================================================
# Loader Class
# =============================================================================

class LongitudinalTestCaseLoader:
    """
    Loader for longitudinal test cases.

    Example:
        loader = LongitudinalTestCaseLoader()
        loader.load()

        # Get all series
        for series in loader.get_all_series():
            print(f"{series.case_name}: {series.num_timepoints} timepoints")

        # Get specific series
        series = loader.get_series("LONG_001")
        t0, t1 = series.get_timepoint_pair("T0", "T1")

        # Get test scenarios
        for scenario in loader.get_test_scenarios():
            print(f"{scenario.scenario_id}: {scenario.description}")
    """

    DEFAULT_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "longitudinal_test_cases" / "longitudinal_cases.json"

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            data_path: Path to longitudinal cases JSON file
        """
        self.data_path = data_path or self.DEFAULT_PATH
        self._data: Optional[Dict[str, Any]] = None
        self._series: Dict[str, LongitudinalSeries] = {}
        self._scenarios: List[TestScenario] = []

    def load(self) -> bool:
        """
        Load longitudinal test cases from JSON file.

        Returns:
            True if successful
        """
        try:
            with open(self.data_path, 'r') as f:
                self._data = json.load(f)

            # Parse series
            for series_data in self._data.get("longitudinal_series", []):
                series = self._parse_series(series_data)
                self._series[series.series_id] = series

            # Parse scenarios
            for scenario_data in self._data.get("test_scenarios", []):
                scenario = TestScenario(
                    scenario_id=scenario_data["scenario_id"],
                    description=scenario_data["description"],
                    series_to_use=scenario_data["series_to_use"],
                    expected_result=scenario_data["expected_result"]
                )
                self._scenarios.append(scenario)

            logger.info(
                f"Loaded {len(self._series)} longitudinal series "
                f"and {len(self._scenarios)} test scenarios"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load longitudinal test cases: {e}")
            return False

    def _parse_series(self, data: Dict[str, Any]) -> LongitudinalSeries:
        """Parse a series from JSON data."""
        timepoints = []
        for tp_data in data.get("timepoints", []):
            tp = Timepoint(
                timepoint_id=tp_data["timepoint_id"],
                date=tp_data["date"],
                day_offset=tp_data["day_offset"],
                study_type=tp_data["study_type"],
                clinical_note=tp_data["clinical_note"],
                synthetic_findings=tp_data["synthetic_findings"],
                impression=tp_data["impression"],
                measurements=tp_data.get("measurements", {})
            )
            timepoints.append(tp)

        expected_changes = []
        for change_data in data.get("expected_changes", []):
            change = ExpectedChange(
                from_timepoint=change_data["from"],
                to_timepoint=change_data["to"],
                change_type=change_data["change_type"],
                findings=change_data["findings"]
            )
            expected_changes.append(change)

        return LongitudinalSeries(
            series_id=data["series_id"],
            case_name=data["case_name"],
            description=data["description"],
            clinical_context=data["clinical_context"],
            expected_outcome=data["expected_outcome"],
            timepoints=timepoints,
            expected_changes=expected_changes
        )

    def get_series(self, series_id: str) -> Optional[LongitudinalSeries]:
        """Get a specific series by ID."""
        return self._series.get(series_id)

    def get_all_series(self) -> List[LongitudinalSeries]:
        """Get all loaded series."""
        return list(self._series.values())

    def get_test_scenarios(self) -> List[TestScenario]:
        """Get all test scenarios."""
        return self._scenarios

    def get_series_by_outcome(self, outcome: str) -> List[LongitudinalSeries]:
        """
        Get series by expected outcome.

        Args:
            outcome: "improvement", "stable", or "worsening"

        Returns:
            List of matching series
        """
        return [s for s in self._series.values() if s.expected_outcome == outcome]

    def get_series_by_study_type(self, study_type: str) -> List[LongitudinalSeries]:
        """
        Get series containing a specific study type.

        Args:
            study_type: "chest_xray" or "ct_chest"

        Returns:
            List of matching series
        """
        result = []
        for series in self._series.values():
            if any(tp.study_type == study_type for tp in series.timepoints):
                result.append(series)
        return result

    def get_metadata(self) -> Dict[str, Any]:
        """Get dataset metadata."""
        if self._data:
            return self._data.get("_metadata", {})
        return {}

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of loaded data."""
        if not self._series:
            return {"loaded": False}

        total_timepoints = sum(s.num_timepoints for s in self._series.values())
        outcomes = {}
        study_types = {}

        for series in self._series.values():
            outcomes[series.expected_outcome] = outcomes.get(series.expected_outcome, 0) + 1
            for tp in series.timepoints:
                study_types[tp.study_type] = study_types.get(tp.study_type, 0) + 1

        return {
            "loaded": True,
            "num_series": len(self._series),
            "total_timepoints": total_timepoints,
            "num_scenarios": len(self._scenarios),
            "outcomes_distribution": outcomes,
            "study_types_distribution": study_types
        }


# =============================================================================
# Utility Functions
# =============================================================================

def create_comparison_prompt(
    series: LongitudinalSeries,
    from_id: str,
    to_id: str
) -> str:
    """
    Create a prompt for longitudinal comparison.

    Args:
        series: The longitudinal series
        from_id: Earlier timepoint ID
        to_id: Later timepoint ID

    Returns:
        Formatted comparison prompt
    """
    pair = series.get_timepoint_pair(from_id, to_id)
    if not pair:
        return ""

    from_tp, to_tp = pair

    prompt = f"""Compare the following two sequential imaging studies:

Clinical Context: {series.clinical_context}

STUDY 1 ({from_tp.date}):
Clinical Note: {from_tp.clinical_note}
Findings:
{chr(10).join('- ' + f for f in from_tp.synthetic_findings)}
Impression: {from_tp.impression}

STUDY 2 ({to_tp.date}):
Clinical Note: {to_tp.clinical_note}
Findings:
{chr(10).join('- ' + f for f in to_tp.synthetic_findings)}
Impression: {to_tp.impression}

Please analyze the interval changes between these studies and provide:
1. Summary of changes
2. Assessment of trajectory (improving, stable, worsening)
3. Clinical recommendations"""

    return prompt


def validate_comparison_result(
    series: LongitudinalSeries,
    from_id: str,
    to_id: str,
    detected_change_type: str
) -> Dict[str, Any]:
    """
    Validate that detected change matches expected change.

    Args:
        series: The longitudinal series
        from_id: Earlier timepoint ID
        to_id: Later timepoint ID
        detected_change_type: What the model detected

    Returns:
        Validation result dictionary
    """
    expected = None
    for change in series.expected_changes:
        if change.from_timepoint == from_id and change.to_timepoint == to_id:
            expected = change
            break

    if not expected:
        return {
            "valid": False,
            "error": f"No expected change defined for {from_id} -> {to_id}"
        }

    is_correct = detected_change_type.lower() == expected.change_type.lower()

    return {
        "valid": True,
        "correct": is_correct,
        "expected_change_type": expected.change_type,
        "detected_change_type": detected_change_type,
        "expected_findings": expected.findings
    }


# =============================================================================
# Main Entry Point
# =============================================================================

def load_longitudinal_cases(
    data_path: Optional[Path] = None
) -> LongitudinalTestCaseLoader:
    """
    Convenience function to load longitudinal test cases.

    Args:
        data_path: Optional custom path to JSON file

    Returns:
        Loaded LongitudinalTestCaseLoader instance
    """
    loader = LongitudinalTestCaseLoader(data_path)
    loader.load()
    return loader


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    loader = load_longitudinal_cases()
    print(f"\nSummary: {loader.get_summary()}")

    print("\nAll series:")
    for series in loader.get_all_series():
        print(f"  - {series.series_id}: {series.case_name} ({series.num_timepoints} timepoints)")

    print("\nTest scenarios:")
    for scenario in loader.get_test_scenarios():
        print(f"  - {scenario.scenario_id}: {scenario.description}")
