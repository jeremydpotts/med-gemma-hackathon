# RadAssist Pro - Project Proposal

**Project:** AI-Powered Longitudinal Change Detection & Summarization
**Competition:** Med-Gemma Impact Challenge
**Team Lead:** Jeremy Potts
**Final Selection Date:** January 18, 2026 (Day 8)
**Submission Target:** February 19, 2026
**Last Updated:** January 21, 2026 (Competitive Analysis Update)

---

## Executive Summary

RadAssist Pro is the **first open-source AI application** that automatically detects, quantifies, and summarizes changes between sequential medical images - turning complex longitudinal comparisons into clear, actionable insights for radiologists and patients.

**Innovation Focus:** While 2D chest X-ray analysis is a saturated market (42+ FDA-approved products), **AI-powered longitudinal change detection with natural language summaries** remains an underserved opportunity. RadAssist Pro fills this gap.

**Key Differentiators:**
- **First** open-source tool for automated longitudinal change summarization
- Natural language generation: "The nodule grew from 8mm to 11mm (37% increase)"
- Patient-friendly progress reports alongside clinical documentation
- Production-ready architecture with HIPAA compliance
- Built on MedGemma 1.5's unique temporal comparison capabilities

**Evaluation Score:** 84/100 (A Grade)
**Selection Confidence:** 8/10 (High)

---

## Competitive Analysis Summary

> **See full analysis:** [COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md)

### Market Reality Check

| Capability | Market Status | Our Strategy |
|------------|--------------|--------------|
| 2D Chest X-ray | **Saturated** (Lunit, Qure.ai, Oxipit) | Supporting feature only |
| 3D Volumetric | **Competitive** (Pillar-0 outperforms MedGemma) | Deprioritized |
| Longitudinal AI Comparison | **Underserved** | **PRIMARY DIFFERENTIATOR** |

### Why Longitudinal is Our Edge

Existing commercial products (Rad AI Continuity, Quantib) focus on **workflow management** (tracking follow-ups), not **AI-powered change detection and summarization**. RadAssist Pro generates actionable insights, not just alerts.

---

## Problem Statement

### The Challenge

**Longitudinal comparison is the most time-consuming part of radiology workflow.**

Radiology departments face critical challenges with serial imaging:

1. **Manual Comparison Burden:** Radiologists spend 15-30% of read time comparing to prior studies
2. **Inconsistent Documentation:** Change descriptions vary widely between radiologists
3. **Missed Progression:** Subtle changes across timepoints are frequently overlooked
4. **Patient Communication Gap:** Patients receive complex reports without understanding their progress
5. **No Automated Summarization:** Existing tools show images side-by-side but don't explain changes

### Why This Matters

- **Cancer surveillance:** 40% of lung cancer patients require serial CT monitoring
- **Treatment response:** Oncology needs quantified change metrics, not subjective descriptions
- **Chronic disease:** Heart failure, COPD patients need longitudinal tracking
- **Patient engagement:** Patients deserve to understand "Am I getting better or worse?"

---

## Solution Overview

### RadAssist Pro Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RadAssist Pro                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  2D Analysis │  │ 3D Volumetric│  │ Longitudinal         │  │
│  │              │  │              │  │ Comparison           │  │
│  │ • Chest X-ray│  │ • CT Volumes │  │ • Disease tracking   │  │
│  │ • Detection  │  │ • Nodule     │  │ • Change detection   │  │
│  │ • Findings   │  │   measurement│  │ • Trend analysis     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │               │
│         └────────────────┬┴─────────────────────┘               │
│                          │                                       │
│                 ┌────────▼────────┐                             │
│                 │   MedGemma 1.5  │                             │
│                 │      4B         │                             │
│                 └────────┬────────┘                             │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                     │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐            │
│  │  Structured │  │    FHIR     │  │   Report    │            │
│  │  Findings   │  │   Output    │  │  Generator  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### MedGemma Capability Utilization

| Capability | RadAssist Pro Usage | Strategic Priority |
|------------|---------------------|-------------------|
| **Longitudinal** | AI-powered change detection & summarization | **PRIMARY - Our differentiator** |
| **2D Analysis** | Single image analysis (supporting) | Secondary - demonstrates MedGemma |
| **3D Volumetric** | Future enhancement | Stretch - deprioritized per competitive analysis |

**Why Longitudinal First:** MedGemma 1.5 shows 5% improvement on longitudinal benchmarks (MS-CXR-T: 66% vs 61%). This is the capability where MedGemma has the clearest advantage and where commercial market gaps exist.

---

## Feature Specification

### MVP Features (Must Have) - REVISED

1. **Longitudinal Change Detection** (PRIMARY FEATURE)
   - Upload two chest X-rays from different dates
   - AI-powered automated change detection
   - Natural language change summary generation
   - Side-by-side visualization with difference highlighting
   - Quantified measurements when possible ("grew from Xmm to Ymm")

2. **Basic 2D Analysis** (SUPPORTING FEATURE)
   - Single image analysis to demonstrate MedGemma works
   - Structured findings output
   - Not the differentiator - keep simple

3. **Comparison Report Generation**
   - Standardized comparison report format
   - Findings and impression sections
   - Prominent AI disclaimer
   - Export to PDF/text

3. **Streamlit User Interface**
   - Clean, professional design
   - Image upload with preview
   - Results display with confidence bars
   - Side-by-side original and annotated view

4. **Test Suite & Documentation**
   - 80%+ code coverage
   - Comprehensive user guide
   - API documentation
   - Setup instructions

### Target Features (Should Have)

1. **Longitudinal Comparison**
   - Upload multiple studies from different dates
   - Automated change detection
   - Side-by-side visualization
   - Change summary generation
   - Progression/stability/improvement classification

2. **Enhanced Visualization**
   - Bounding boxes for findings
   - Heat maps for areas of concern
   - Measurement tools
   - Comparison overlays

3. **FHIR Integration**
   - DiagnosticReport resource generation
   - Observation resources for findings
   - ICD-10 code mapping
   - HL7 compliance

### Stretch Features (Nice to Have)

1. **3D Volumetric Analysis**
   - CT/MRI volume upload
   - Slice-by-slice navigation
   - Volumetric measurements
   - Nodule detection and sizing
   - 3D rendering

2. **Advanced Longitudinal**
   - Automated measurement comparison
   - Growth rate calculations
   - Risk assessment based on trends
   - Treatment response evaluation

---

## Technical Architecture

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **AI Model** | MedGemma 1.5 4B | Competition requirement, multimodal |
| **Backend** | Python 3.9+ | Data science standard |
| **UI Framework** | Streamlit | Rapid development, medical demos |
| **Image Processing** | PIL, pydicom, SimpleITK | Medical image support |
| **Security** | Custom HIPAA module | Healthcare compliance |
| **Testing** | pytest | Industry standard |
| **Data Format** | DICOM, NIfTI, PNG/JPEG | Medical imaging standards |

### Key Components

```
src/
├── models/
│   ├── medgemma_wrapper.py    # Model interface (complete)
│   └── inference.py           # Inference pipeline (complete)
├── data/
│   ├── loaders.py             # Data loading (complete)
│   ├── preprocessing.py       # Image preprocessing
│   └── longitudinal_loader.py # Longitudinal test cases (complete)
├── security/
│   ├── hipaa_compliance.py    # HIPAA module (complete)
│   ├── audit_log.py           # Audit logging (complete)
│   └── deidentification.py    # PHI removal (complete)
├── utils/
│   ├── medical_utils.py       # Medical utilities (complete)
│   └── visualization.py       # Visualization tools (complete)
└── app/
    └── streamlit_app.py       # Main UI (framework complete)
```

### Current Implementation Status

| Component | Status | Tests |
|-----------|--------|-------|
| MedGemma Wrapper | ✅ Complete | 25 tests |
| HIPAA Security | ✅ Complete | 30 tests |
| Data Loaders | ✅ Complete | 15 tests |
| Visualization | ✅ Complete | 10 tests |
| Medical Utils | ✅ Complete | 12 tests |
| Streamlit UI | ✅ Framework | 8 tests |
| Longitudinal Loader | ✅ Complete | 36 tests |
| **Total** | **60%+ Complete** | **119 tests** |

---

## Data Requirements

### Training/Testing Data

| Data Type | Source | Purpose | Status |
|-----------|--------|---------|--------|
| Chest X-rays | NIH ChestX-ray14 | 2D analysis testing | Available |
| CT Volumes | TCIA (The Cancer Imaging Archive) | 3D analysis testing | Registration needed |
| Longitudinal Sets | Synthetic generation | Longitudinal testing | ✅ Created |
| Ground Truth | Public datasets | Validation | Available |

### Synthetic Longitudinal Test Cases

Five comprehensive longitudinal series created:
1. **LONG_001:** Pneumonia resolution (improvement)
2. **LONG_002:** Pulmonary nodule surveillance (stable)
3. **LONG_003:** Heart failure progression (worsening then improvement)
4. **LONG_004:** Post-surgical monitoring (improvement)
5. **LONG_005:** Lung nodule growth (concerning, worsening)

---

## Implementation Timeline

### Phase 3: Core Development (Days 11-25)

| Days | Focus | Deliverables |
|------|-------|--------------|
| 11-13 | 2D Prototype | Working 2D inference, basic UI |
| 14-17 | Longitudinal | Comparison logic, side-by-side view |
| 18-21 | 3D Volumetric (Stretch) | Volume analysis, measurements |
| 22-25 | Testing | Comprehensive validation |

**Feature Freeze: Day 17**

### Phase 4: Refinement (Days 26-32)

| Days | Focus | Deliverables |
|------|-------|--------------|
| 26-28 | UI Polish | Professional appearance |
| 29-30 | Documentation | Complete user guide |
| 31-32 | Demo Materials | Video, presentation |

### Phase 5: Submission (Days 33-37)

| Days | Focus | Deliverables |
|------|-------|--------------|
| 33-34 | Final Testing | End-to-end validation |
| 35-36 | Submission Prep | Package, verify requirements |
| 37 | **SUBMIT** | February 19, 2026 |

---

## Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 3D too complex | 40% | Medium | Fallback to 2D + longitudinal |
| Performance issues | 25% | High | Quantization, caching |
| Time overrun | 35% | Medium | Feature freeze Day 17, 5-day buffer |
| Accuracy concerns | 30% | Medium | Prominent disclaimers, expert feedback |

### Fallback Strategy

- **If 3D fails:** 2D + longitudinal still demonstrates unique capabilities
- **If longitudinal fails:** Strong 2D with excellent UX still competitive
- **Worst case:** Polished 2D chest X-ray tool with proper documentation

---

## Success Criteria

### Minimum Viable Product (Must Achieve)
- [ ] 2D chest X-ray analysis working
- [ ] Basic report generation
- [ ] Clean, functional UI
- [ ] Test suite passing
- [ ] Documentation complete
- [ ] Demo video recorded
- [ ] Submitted on time

### Target (Should Achieve)
- [ ] All MVP requirements
- [ ] Longitudinal comparison working
- [ ] Side-by-side visualization
- [ ] Change detection
- [ ] 80%+ test coverage
- [ ] Professional polish

### Stretch (Nice to Have)
- [ ] All Target requirements
- [ ] 3D volumetric analysis
- [ ] Volume measurements
- [ ] Clinical expert review obtained
- [ ] Exceptional demo quality

---

## Competition Alignment

### How RadAssist Pro Wins

1. **Showcases MedGemma Uniqueness**
   - Only submission using ALL THREE capabilities (2D, 3D, longitudinal)
   - Demonstrates capabilities no competitor model can match

2. **Clear Clinical Impact**
   - Addresses real radiology workflow problems
   - Saves radiologist time
   - Catches potentially missed findings
   - Enables disease progression tracking

3. **Technical Excellence**
   - Production-ready architecture
   - HIPAA compliance built-in
   - Comprehensive testing
   - Clean, maintainable code

4. **Professional Presentation**
   - Polished UI/UX
   - Clear documentation
   - Compelling demo narrative
   - Real-world deployment considerations

---

## Team & Resources

### Team
- **Jeremy Potts** - CEO, Competition Lead, Development
- **Claude (AI Assistant)** - Development Support

### Compute Resources
- Development: MacOS local machine
- Testing: CPU inference (mock mode available)
- Production demo: Cloud GPU if needed

### External Resources
- MedGemma model via Hugging Face
- Public medical imaging datasets
- Clinical validation (informal expert feedback)

---

## Appendix

### A. Evaluation Scoring Details

| Criterion | Score | Max | Notes |
|-----------|-------|-----|-------|
| Clinical Impact | 22 | 25 | Addresses high-volume radiology needs |
| Technical Innovation | 17 | 20 | Uses all 3 MedGemma capabilities |
| Feasibility | 16 | 20 | 60%+ already built |
| User-Centered Design | 12 | 15 | Streamlit UI, clean workflow |
| Competition Alignment | 9 | 10 | Perfect MedGemma showcase |
| Scalability | 8 | 10 | Modular, cloud-ready |
| **Total** | **84** | **100** | **A Grade** |

### B. References

- MedGemma Documentation: [Google HAI-DEF](https://developers.google.com/health-ai)
- NIH ChestX-ray14: [Dataset](https://nihcc.app.box.com/v/ChestXray-NIHCC)
- TCIA: [The Cancer Imaging Archive](https://www.cancerimagingarchive.net/)
- FHIR: [HL7 FHIR Standard](https://www.hl7.org/fhir/)

---

**Document Version:** 1.0
**Last Updated:** January 18, 2026
**Status:** APPROVED ✅
