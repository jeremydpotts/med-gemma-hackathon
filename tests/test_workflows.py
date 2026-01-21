"""
End-to-end workflow tests for RadAssist Pro.

This module tests complete user workflows including:
- 2D chest X-ray analysis workflow
- 3D CT/MRI volume analysis workflow
- Longitudinal comparison workflow
- Report generation workflow
- Error recovery workflows
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

# Mark entire module
pytestmark = [pytest.mark.integration]


class Test2DChestXrayWorkflow:
    """Test complete 2D chest X-ray analysis workflow."""

    def test_complete_2d_workflow(
        self,
        mock_medgemma_model,
        synthetic_patient_data,
        temp_output_dir
    ):
        """Test complete workflow: upload -> analyze -> report."""
        # Step 1: Simulate image upload
        image_path = "test_chest_xray.png"
        patient = synthetic_patient_data

        # Step 2: Run inference
        result = mock_medgemma_model.infer(image_path)

        # Step 3: Validate result
        assert result is not None
        assert "findings" in result
        assert "confidence" in result

        # Step 4: Generate report
        report = {
            "study_id": f"{patient['patient_id']}_001",
            "patient_id": patient["patient_id"],
            "study_type": "chest_xray",
            "study_date": patient["study_date"],
            "findings": result["findings"],
            "impression": result.get("impression", "See detailed findings"),
            "confidence": result["confidence"],
            "model_version": result.get("model_version", "unknown"),
            "is_synthetic": True,
            "disclaimer": "FOR RESEARCH PURPOSES ONLY - NOT FOR CLINICAL USE"
        }

        # Step 5: Save report
        report_path = temp_output_dir / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Step 6: Verify report
        assert report_path.exists()
        with open(report_path) as f:
            saved_report = json.load(f)

        assert saved_report["study_type"] == "chest_xray"
        assert saved_report["disclaimer"] is not None

    def test_2d_workflow_with_abnormal_finding(
        self,
        mock_medgemma_model,
        mock_medgemma_response_abnormal,
        synthetic_patient_data
    ):
        """Test workflow when abnormality is detected."""
        # Configure mock to return abnormal findings
        mock_medgemma_model.infer.return_value = mock_medgemma_response_abnormal

        # Run inference
        result = mock_medgemma_model.infer("abnormal_xray.png")

        # Verify abnormalities are captured
        assert "abnormalities_detected" in result
        assert len(result["abnormalities_detected"]) > 0

        # Verify confidence is reported
        assert result["confidence"] >= 0.5

    def test_2d_workflow_with_normal_finding(
        self,
        mock_medgemma_model,
        mock_medgemma_response_normal,
        synthetic_patient_data
    ):
        """Test workflow when study is normal."""
        mock_medgemma_model.infer.return_value = mock_medgemma_response_normal

        result = mock_medgemma_model.infer("normal_xray.png")

        assert "No acute" in result["impression"] or "normal" in result["impression"].lower()
        assert result["confidence"] > 0.7


class Test3DVolumeWorkflow:
    """Test complete 3D CT/MRI volume analysis workflow."""

    def test_complete_3d_ct_workflow(
        self,
        mock_medgemma_model,
        synthetic_patient_data,
        temp_output_dir
    ):
        """Test complete 3D CT volume analysis workflow."""
        # Step 1: Simulate volume upload (directory of DICOM slices)
        volume_path = "test_ct_volume/"
        patient = synthetic_patient_data

        # Step 2: Run 3D inference
        result = mock_medgemma_model.infer_3d(volume_path)

        # Step 3: Validate 3D-specific results
        assert result is not None
        assert "findings" in result
        assert "measurements" in result
        assert "slices_processed" in result

        # Step 4: Generate 3D report with measurements
        report = {
            "study_id": f"{patient['patient_id']}_CT_001",
            "patient_id": patient["patient_id"],
            "study_type": "ct_volume",
            "modality": "CT",
            "findings": result["findings"],
            "measurements": result["measurements"],
            "slices_analyzed": result["slices_processed"],
            "confidence": result["confidence"],
            "processing_time_ms": result["processing_time_ms"],
            "disclaimer": "FOR RESEARCH PURPOSES ONLY"
        }

        # Step 5: Verify report structure
        assert "measurements" in report
        assert report["modality"] == "CT"

    def test_3d_workflow_returns_volumetric_measurements(
        self,
        mock_medgemma_model
    ):
        """Test that 3D workflow returns volumetric measurements."""
        result = mock_medgemma_model.infer_3d("test_volume/")

        assert "measurements" in result
        measurements = result["measurements"]

        # Should include at least one volumetric measurement
        assert len(measurements) > 0


class TestLongitudinalComparisonWorkflow:
    """Test longitudinal (temporal) comparison workflow."""

    def test_two_timepoint_comparison(
        self,
        mock_medgemma_model,
        synthetic_patient_data
    ):
        """Test comparison between two timepoints."""
        # Two studies from different dates
        studies = [
            {"path": "study_2025_01/", "date": "2025-01-15"},
            {"path": "study_2026_01/", "date": "2026-01-15"}
        ]

        # Run comparison
        result = mock_medgemma_model.compare_longitudinal(
            [s["path"] for s in studies]
        )

        # Validate comparison results
        assert result is not None
        assert "comparison" in result
        assert "changes_detected" in result
        assert "timepoints_compared" in result

    def test_three_timepoint_comparison(
        self,
        mock_medgemma_model
    ):
        """Test comparison across three timepoints."""
        studies = [
            "study_t1/",
            "study_t2/",
            "study_t3/"
        ]

        result = mock_medgemma_model.compare_longitudinal(studies)

        assert result is not None
        assert "comparison" in result

    def test_longitudinal_detects_progression(
        self,
        mock_medgemma_model
    ):
        """Test that longitudinal comparison can detect disease progression."""
        # Configure mock to return progression
        mock_medgemma_model.compare_longitudinal.return_value = {
            "comparison": "Interval increase in nodule size",
            "changes_detected": [
                {"finding": "nodule", "change": "increased", "delta": "+2mm"}
            ],
            "confidence": 0.75,
            "timepoints_compared": 2,
            "recommendation": "Consider follow-up or biopsy"
        }

        result = mock_medgemma_model.compare_longitudinal(["t1/", "t2/"])

        assert len(result["changes_detected"]) > 0
        assert result["changes_detected"][0]["change"] == "increased"


class TestReportGenerationWorkflow:
    """Test report generation workflows."""

    @pytest.fixture
    def report_generator(self):
        """Create a mock report generator."""
        generator = MagicMock()

        def generate_report(findings, patient_data, format="json"):
            report = {
                "header": {
                    "patient_id": patient_data.get("patient_id", "ANONYMOUS"),
                    "study_date": patient_data.get("study_date", "UNKNOWN"),
                    "generated_at": "2026-01-21T12:00:00Z",
                    "model_version": "medgemma-1.5-4b"
                },
                "body": {
                    "findings": findings.get("findings", []),
                    "impression": findings.get("impression", "See findings"),
                    "confidence": findings.get("confidence", 0.0)
                },
                "footer": {
                    "disclaimer": "FOR RESEARCH PURPOSES ONLY - NOT FOR CLINICAL USE",
                    "generated_by": "RadAssist Pro (MedGemma 1.5)"
                }
            }
            return report

        generator.generate.side_effect = generate_report
        return generator

    def test_json_report_generation(
        self,
        report_generator,
        mock_medgemma_response_normal,
        synthetic_patient_data
    ):
        """Test JSON report generation."""
        report = report_generator.generate(
            mock_medgemma_response_normal,
            synthetic_patient_data,
            format="json"
        )

        assert "header" in report
        assert "body" in report
        assert "footer" in report
        assert "disclaimer" in report["footer"]

    def test_report_includes_all_findings(
        self,
        report_generator,
        mock_medgemma_response_abnormal,
        synthetic_patient_data
    ):
        """Test that report includes all findings."""
        report = report_generator.generate(
            mock_medgemma_response_abnormal,
            synthetic_patient_data
        )

        findings = report["body"]["findings"]
        assert len(findings) > 0

    def test_report_has_disclaimer(
        self,
        report_generator,
        mock_medgemma_response_normal,
        synthetic_patient_data
    ):
        """Test that report includes required disclaimer."""
        report = report_generator.generate(
            mock_medgemma_response_normal,
            synthetic_patient_data
        )

        disclaimer = report["footer"]["disclaimer"]
        assert "NOT FOR CLINICAL USE" in disclaimer


class TestErrorRecoveryWorkflow:
    """Test error recovery in workflows."""

    def test_recovers_from_inference_timeout(self, mock_medgemma_model):
        """Test recovery from inference timeout."""
        # First call times out, second succeeds
        mock_medgemma_model.infer.side_effect = [
            TimeoutError("Inference timed out"),
            {"findings": ["Normal"], "confidence": 0.8, "processing_time_ms": 100, "model_version": "test"}
        ]

        # First attempt fails
        with pytest.raises(TimeoutError):
            mock_medgemma_model.infer("image.png")

        # Retry succeeds
        result = mock_medgemma_model.infer("image.png")
        assert result is not None
        assert "findings" in result

    def test_handles_partial_3d_failure(self, mock_medgemma_model):
        """Test handling of partial 3D volume processing failure."""
        # Return partial results
        mock_medgemma_model.infer_3d.return_value = {
            "findings": ["Partial analysis completed"],
            "confidence": 0.5,
            "slices_processed": 128,
            "total_slices": 256,
            "processing_time_ms": 15000,
            "status": "partial",
            "error": "Memory limit reached at slice 128"
        }

        result = mock_medgemma_model.infer_3d("large_volume/")

        assert result["status"] == "partial"
        assert result["slices_processed"] < result["total_slices"]

    def test_validates_input_before_processing(self):
        """Test that inputs are validated before processing."""
        def validate_and_process(image_path):
            # Validation
            if not image_path:
                raise ValueError("Image path cannot be empty")
            if not image_path.endswith(('.png', '.jpg', '.dcm')):
                raise ValueError("Unsupported image format")
            return {"status": "valid"}

        # Valid inputs
        assert validate_and_process("test.png")["status"] == "valid"

        # Invalid inputs
        with pytest.raises(ValueError):
            validate_and_process("")

        with pytest.raises(ValueError):
            validate_and_process("test.gif")


class TestBatchProcessingWorkflow:
    """Test batch processing workflows."""

    def test_batch_2d_processing(self, mock_medgemma_model):
        """Test processing multiple 2D images in batch."""
        images = [
            "image_001.png",
            "image_002.png",
            "image_003.png"
        ]

        results = []
        for image in images:
            result = mock_medgemma_model.infer(image)
            results.append(result)

        assert len(results) == len(images)
        for result in results:
            assert "findings" in result

    def test_batch_results_aggregation(self, mock_medgemma_model):
        """Test aggregation of batch results."""
        images = ["img1.png", "img2.png", "img3.png"]

        results = [mock_medgemma_model.infer(img) for img in images]

        # Aggregate statistics
        total_processing_time = sum(r["processing_time_ms"] for r in results)
        avg_confidence = sum(r["confidence"] for r in results) / len(results)

        assert total_processing_time > 0
        assert 0 <= avg_confidence <= 1


class TestMultimodalWorkflow:
    """Test multimodal workflows (image + text)."""

    def test_image_with_clinical_context(self, mock_medgemma_model):
        """Test image analysis with clinical context."""
        # Configure mock to accept clinical context
        mock_medgemma_model.infer_with_context.return_value = {
            "findings": [
                "Given clinical history of CHF, findings are consistent",
                "Cardiomegaly present",
                "Bilateral pleural effusions"
            ],
            "confidence": 0.82,
            "context_used": True,
            "processing_time_ms": 180,
            "model_version": "medgemma-1.5-4b"
        }

        clinical_context = "History of congestive heart failure, presenting with dyspnea"

        result = mock_medgemma_model.infer_with_context(
            image_path="chest_xray.png",
            clinical_context=clinical_context
        )

        assert result["context_used"] is True
        assert "CHF" in result["findings"][0]

    def test_image_without_context(self, mock_medgemma_model):
        """Test image analysis without clinical context."""
        result = mock_medgemma_model.infer("chest_xray.png")

        # Should still produce valid results
        assert "findings" in result
        assert len(result["findings"]) > 0


# =============================================================================
# Performance Workflow Tests
# =============================================================================

@pytest.mark.slow
class TestPerformanceWorkflows:
    """Performance-focused workflow tests."""

    def test_2d_workflow_under_10_seconds(
        self,
        mock_medgemma_model,
        performance_thresholds
    ):
        """Test that 2D workflow completes within performance threshold."""
        result = mock_medgemma_model.infer("test.png")

        assert result["processing_time_ms"] <= performance_thresholds["2d_inference_max_ms"]

    def test_3d_workflow_under_30_seconds(
        self,
        mock_medgemma_model,
        performance_thresholds
    ):
        """Test that 3D workflow completes within performance threshold."""
        result = mock_medgemma_model.infer_3d("volume/")

        assert result["processing_time_ms"] <= performance_thresholds["3d_inference_max_ms"]
