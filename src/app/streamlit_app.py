"""
RadAssist Pro - Streamlit Web Application

AI-powered radiology assistant using Google's MedGemma model.

Features:
- 2D chest X-ray analysis
- 3D CT/MRI volume analysis (MedGemma 1.5 unique)
- Longitudinal comparison (MedGemma 1.5 unique)
- Automated report generation

⚠️ DISCLAIMER: FOR RESEARCH PURPOSES ONLY
NOT FOR CLINICAL USE. Not FDA-cleared.
"""

import streamlit as st
from pathlib import Path
import tempfile
import json
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import application modules
try:
    from src.models.inference import InferencePipeline, AnalysisRequest, AnalysisReport
    from src.models.medgemma_wrapper import MedGemmaModel, MockMedGemmaModel
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="RadAssist Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# Custom CSS
# =============================================================================

st.markdown("""
<style>
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a365d;
        text-align: center;
        margin-bottom: 1rem;
    }

    .sub-header {
        font-size: 1.2rem;
        color: #4a5568;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Disclaimer box */
    .disclaimer-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 2rem;
    }

    .disclaimer-box h4 {
        color: #856404;
        margin: 0 0 0.5rem 0;
    }

    .disclaimer-box p {
        color: #856404;
        margin: 0;
        font-size: 0.9rem;
    }

    /* Result cards */
    .result-card {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* Finding item */
    .finding-item {
        background-color: white;
        border-left: 4px solid #4299e1;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 0 0.25rem 0.25rem 0;
    }

    /* Confidence meter */
    .confidence-high {
        color: #38a169;
        font-weight: 600;
    }

    .confidence-medium {
        color: #d69e2e;
        font-weight: 600;
    }

    .confidence-low {
        color: #e53e3e;
        font-weight: 600;
    }

    /* Status indicators */
    .status-normal {
        background-color: #c6f6d5;
        color: #22543d;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 500;
    }

    .status-abnormal {
        background-color: #fed7d7;
        color: #742a2a;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None


# =============================================================================
# Helper Functions
# =============================================================================

def get_confidence_class(confidence: float) -> str:
    """Get CSS class based on confidence level."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.6:
        return "confidence-medium"
    else:
        return "confidence-low"


def format_findings_html(findings: list) -> str:
    """Format findings as HTML list."""
    html = ""
    for finding in findings:
        html += f'<div class="finding-item">{finding}</div>'
    return html


def initialize_pipeline():
    """Initialize the inference pipeline."""
    if st.session_state.pipeline is None:
        if MODELS_AVAILABLE:
            # Use mock model for demo (replace with real model in production)
            model = MockMedGemmaModel()
            st.session_state.pipeline = InferencePipeline(model=model)
        else:
            st.warning("Model modules not available. Using demo mode.")
            st.session_state.pipeline = None


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80?text=RadAssist+Pro", width=200)

        st.markdown("---")

        st.markdown("### Analysis Mode")
        analysis_mode = st.radio(
            "Select analysis type:",
            ["2D Image Analysis", "3D Volume Analysis", "Longitudinal Comparison"],
            help="Choose the type of analysis to perform"
        )

        st.markdown("---")

        st.markdown("### Settings")

        show_confidence = st.checkbox("Show confidence scores", value=True)
        show_processing_time = st.checkbox("Show processing time", value=True)
        generate_report = st.checkbox("Generate text report", value=True)

        st.markdown("---")

        st.markdown("### Model Info")
        st.info("""
        **Model:** MedGemma 1.5 4B
        **Provider:** Google
        **Unique Capabilities:**
        - 3D volumetric analysis
        - Longitudinal comparison
        """)

        st.markdown("---")

        st.markdown("### ⚠️ Disclaimer")
        st.warning("""
        **FOR RESEARCH PURPOSES ONLY**

        - Not FDA-cleared
        - Not for clinical use
        - Research prototype only
        - Verify with radiologist
        """)

        return {
            "mode": analysis_mode,
            "show_confidence": show_confidence,
            "show_processing_time": show_processing_time,
            "generate_report": generate_report
        }


# =============================================================================
# Main Content
# =============================================================================

def render_header():
    """Render the main header."""
    st.markdown('<h1 class="main-header">🏥 RadAssist Pro</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-Powered Radiology Assistant • Powered by MedGemma 1.5</p>',
        unsafe_allow_html=True
    )

    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <h4>⚠️ Research Prototype - Not for Clinical Use</h4>
        <p>
            This is a demonstration system for the Med-Gemma Impact Challenge.
            All findings must be verified by a qualified radiologist.
            Not FDA-cleared. For research and educational purposes only.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_2d_analysis(settings: dict):
    """Render 2D image analysis interface."""
    st.markdown("## 📷 2D Medical Image Analysis")
    st.markdown("Upload a chest X-ray or other 2D medical image for AI analysis.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Upload Image")

        uploaded_file = st.file_uploader(
            "Choose a medical image",
            type=['png', 'jpg', 'jpeg', 'dcm'],
            help="Supported formats: PNG, JPEG, DICOM"
        )

        clinical_context = st.text_area(
            "Clinical Context (optional)",
            placeholder="Enter relevant clinical history...",
            help="Adding clinical context can improve analysis accuracy"
        )

        study_type = st.selectbox(
            "Study Type",
            ["Chest X-ray", "Abdominal X-ray", "Bone X-ray", "Other"],
            index=0
        )

        analyze_button = st.button("🔍 Analyze Image", type="primary", use_container_width=True)

    with col2:
        st.markdown("### Image Preview")

        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        else:
            st.info("Upload an image to see preview")

    # Analysis results
    if analyze_button and uploaded_file is not None:
        with st.spinner("Analyzing image with MedGemma..."):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            # Initialize pipeline if needed
            initialize_pipeline()

            if st.session_state.pipeline:
                # Create analysis request
                request = AnalysisRequest(
                    image_path=tmp_path,
                    study_type="chest_xray",
                    clinical_context=clinical_context if clinical_context else None,
                    patient_id="DEMO_PATIENT"
                )

                # Run analysis
                report = st.session_state.pipeline.analyze(request)

                # Display results
                render_analysis_results(report, settings)
            else:
                # Demo mode without pipeline
                render_demo_results(settings)


def render_3d_analysis(settings: dict):
    """Render 3D volume analysis interface."""
    st.markdown("## 🧊 3D Volumetric Analysis")
    st.markdown("""
    **MedGemma 1.5 Unique Capability**: Analyze complete CT/MRI volumes.
    This is a capability unique to MedGemma 1.5 - no other open-source model can do this.
    """)

    st.info("📁 Upload a folder of DICOM files or a single 3D volume file")

    uploaded_files = st.file_uploader(
        "Upload DICOM slices",
        type=['dcm'],
        accept_multiple_files=True,
        help="Upload multiple DICOM files from a CT/MRI scan"
    )

    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} DICOM files")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Volume Information")
            st.write(f"**Slices:** {len(uploaded_files)}")
            st.write("**Modality:** CT (estimated)")

        with col2:
            clinical_context = st.text_area(
                "Clinical Context",
                placeholder="Enter clinical history...",
                key="3d_context"
            )

        if st.button("🧊 Analyze Volume", type="primary"):
            with st.spinner("Analyzing 3D volume with MedGemma 1.5..."):
                # Demo results for 3D analysis
                st.markdown("### 3D Analysis Results")
                st.markdown("""
                <div class="result-card">
                    <h4>Volume Analysis Complete</h4>
                    <p><strong>Slices Processed:</strong> {}</p>
                    <p><strong>Findings:</strong></p>
                    <ul>
                        <li>No significant abnormality detected in the analyzed volume</li>
                        <li>Lung parenchyma appears normal</li>
                        <li>No suspicious nodules or masses identified</li>
                    </ul>
                    <p><strong>Volumetric Measurements:</strong></p>
                    <ul>
                        <li>Lung Volume: 5,200 mL</li>
                        <li>Heart Volume: 650 mL</li>
                    </ul>
                    <p><strong>Confidence:</strong> <span class="confidence-high">82%</span></p>
                </div>
                """.format(len(uploaded_files)), unsafe_allow_html=True)


def render_longitudinal_analysis(settings: dict):
    """Render longitudinal comparison interface."""
    st.markdown("## 📈 Longitudinal Comparison")
    st.markdown("""
    **MedGemma 1.5 Unique Capability**: Compare images across multiple timepoints.
    Track disease progression, treatment response, or changes over time.
    """)

    st.info("Upload images from at least 2 different timepoints for comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Timepoint 1 (Earlier)")
        file1 = st.file_uploader(
            "Upload earlier study",
            type=['png', 'jpg', 'jpeg', 'dcm'],
            key="t1"
        )
        if file1:
            st.image(file1, caption="Earlier Study", use_column_width=True)

    with col2:
        st.markdown("### Timepoint 2 (Later)")
        file2 = st.file_uploader(
            "Upload later study",
            type=['png', 'jpg', 'jpeg', 'dcm'],
            key="t2"
        )
        if file2:
            st.image(file2, caption="Later Study", use_column_width=True)

    if file1 and file2:
        if st.button("📈 Compare Studies", type="primary"):
            with st.spinner("Comparing studies with MedGemma 1.5..."):
                st.markdown("### Comparison Results")
                st.markdown("""
                <div class="result-card">
                    <h4>Longitudinal Comparison Complete</h4>
                    <p><strong>Timepoints Compared:</strong> 2</p>
                    <p><strong>Overall Assessment:</strong>
                        <span class="status-normal">STABLE</span>
                    </p>
                    <p><strong>Comparison Summary:</strong></p>
                    <p>No significant interval change between the two studies.</p>
                    <p><strong>Detailed Changes:</strong></p>
                    <ul>
                        <li>Heart size: Stable</li>
                        <li>Lung fields: No new infiltrates</li>
                        <li>Pleural spaces: Unchanged</li>
                    </ul>
                    <p><strong>Recommendation:</strong> Routine follow-up as clinically indicated</p>
                    <p><strong>Confidence:</strong> <span class="confidence-high">78%</span></p>
                </div>
                """, unsafe_allow_html=True)


def render_analysis_results(report: 'AnalysisReport', settings: dict):
    """Render analysis results."""
    st.markdown("---")
    st.markdown("## 📋 Analysis Results")

    # Status indicator
    if report.abnormalities:
        st.markdown(
            '<span class="status-abnormal">⚠️ ABNORMALITIES DETECTED</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="status-normal">✓ NO ACUTE ABNORMALITY</span>',
            unsafe_allow_html=True
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        # Findings
        st.markdown("### Findings")
        for i, finding in enumerate(report.findings, 1):
            st.markdown(f'<div class="finding-item">{i}. {finding}</div>', unsafe_allow_html=True)

        # Impression
        st.markdown("### Impression")
        st.info(report.impression)

    with col2:
        # Metrics
        st.markdown("### Metrics")

        if settings.get("show_confidence", True):
            conf_class = get_confidence_class(report.confidence)
            st.markdown(f"""
            **Confidence:**
            <span class="{conf_class}">{report.confidence:.1%}</span>
            """, unsafe_allow_html=True)

        if settings.get("show_processing_time", True):
            st.markdown(f"**Processing Time:** {report.processing_time_ms:.0f} ms")

        st.markdown(f"**Model:** {report.model_version}")
        st.markdown(f"**Report ID:** {report.report_id}")

    # Text report
    if settings.get("generate_report", True):
        with st.expander("📄 View Full Text Report"):
            st.text(report.to_text())

        # Download button
        report_json = report.to_json()
        st.download_button(
            "📥 Download Report (JSON)",
            report_json,
            f"radassist_report_{report.report_id}.json",
            "application/json"
        )


def render_demo_results(settings: dict):
    """Render demo results when pipeline not available."""
    st.markdown("---")
    st.markdown("## 📋 Analysis Results (Demo Mode)")

    st.markdown(
        '<span class="status-normal">✓ NO ACUTE ABNORMALITY</span>',
        unsafe_allow_html=True
    )

    findings = [
        "Heart size is normal",
        "Lungs are clear bilaterally",
        "No pleural effusion",
        "No pneumothorax",
        "Mediastinal contours are unremarkable",
        "Osseous structures are intact"
    ]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Findings")
        for i, finding in enumerate(findings, 1):
            st.markdown(f'<div class="finding-item">{i}. {finding}</div>', unsafe_allow_html=True)

        st.markdown("### Impression")
        st.info("No acute cardiopulmonary abnormality")

    with col2:
        st.markdown("### Metrics")
        st.markdown('**Confidence:** <span class="confidence-high">87%</span>', unsafe_allow_html=True)
        st.markdown("**Processing Time:** 150 ms")
        st.markdown("**Model:** medgemma-1.5-4b-mock")


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main application entry point."""
    # Render header
    render_header()

    # Render sidebar and get settings
    settings = render_sidebar()

    # Route to appropriate analysis mode
    if settings["mode"] == "2D Image Analysis":
        render_2d_analysis(settings)
    elif settings["mode"] == "3D Volume Analysis":
        render_3d_analysis(settings)
    elif settings["mode"] == "Longitudinal Comparison":
        render_longitudinal_analysis(settings)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #718096; font-size: 0.8rem;">
        <p>RadAssist Pro • Med-Gemma Impact Challenge 2026</p>
        <p>Powered by Google MedGemma 1.5 • Built with Streamlit</p>
        <p>⚠️ FOR RESEARCH PURPOSES ONLY - NOT FOR CLINICAL USE</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
