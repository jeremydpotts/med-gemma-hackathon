# RadAssist Pro - Strategy Advisory Report

**Date:** January 21, 2026
**Contributors:** Product Management Expert, Marketing Expert, Competitive Analysis
**Purpose:** Strategic guidance for Med-Gemma Impact Challenge ($100,000 grand prize)

---

## Executive Summary

Based on expert consultation, we're refining RadAssist Pro's positioning and feature focus:

### Key Strategic Decisions

| Decision | Rationale |
|----------|-----------|
| **Narrow to lung nodule tracking** | Single modality, single finding type = credible scope |
| **Add clinical decision support** | Measurement → risk stratification is the innovation |
| **Tagline: "AI That Remembers"** | Simple, memorable, differentiating |
| **Demo: "The Missed Progression Save"** | Emotional, high-stakes, shows real value |

---

## Product Management Recommendations

### 1. Narrow Further: Lung Nodule Surveillance

**Winning positioning:**
> "AI-powered lung nodule tracking with clinical decision support."

**Why this works:**
- Single modality (CT) - technically tractable
- Single finding type (nodules) - well-defined problem
- Single use case (surveillance) - clear workflow
- Complete solution (measurement + risk + report language)

### 2. Add Clinical Decision Support

**Don't just measure - interpret:**

```
LONGITUDINAL ANALYSIS: Right upper lobe nodule

Timeline:
- 2024-01-15: 8mm solid nodule, Lung-RADS 4A
- 2024-07-20: 11mm solid nodule (+37%, VDT ~185 days)

Change interpretation:
Growth rate suggests intermediate-to-high suspicion.
Volume doubling time <400 days associated with
increased malignancy probability.

Updated differential:
1. Primary lung malignancy (probability INCREASED)
2. Inflammatory/infectious (probability DECREASED)
3. Slow-growing carcinoid (probability STABLE)

Suggested follow-up: Per Lung-RADS 4B, consider
PET-CT or tissue sampling.

[Draft report language] [Patient summary]
```

### 3. Validation Priorities (This Week)

1. **Day 1-2:** Run 5 paired scans through MedGemma - can it identify corresponding anatomy?
2. **Day 3:** Talk to 2-3 radiologists - validate the workflow pain point
3. **Day 4-5:** Build simplest demo: two DICOMs → comparison paragraph
4. **Day 6-7:** Add the "differential timeline" feature (the judge-wower)

### 4. Feature That Makes Judges Say "Innovative"

**"Differential Diagnosis Timeline"**

Not just change detection - show how the differential should evolve based on change patterns. This demonstrates:
- Clinical reasoning, not just measurement
- Understanding of real radiology workflows (Lung-RADS)
- Actionable next steps
- Complete differentiation from "bounding box" competitors

### 5. Product-Market Fit Concerns to Address

| Concern | Mitigation |
|---------|------------|
| Accuracy requirements are brutal | Show "when RadAssist Pro defers to radiologist" |
| Patient communication is crowded | Focus on radiologist-facing first |
| Multi-modality is scope creep | Pick CT-to-CT only |
| Competition is dictation | Target: comparison in <10 seconds |

---

## Marketing Recommendations

### 1. Primary Tagline

**"AI That Remembers"**

Why it works:
- Simple, memorable
- Implies the problem (AI that doesn't track history)
- Human quality applied to technology
- Works across all audiences

### 2. The Winning Narrative

**The Hook (30 seconds):**
> "A 58-year-old patient was told 'stable' four times. She had cancer."

**The Problem:**
> "Radiologists aren't failing at detection—they're drowning in comparison. 15+ minutes per CT comparison × 50 patients × 250 days = the math doesn't work."

**The Insight:**
> "Detection is solved. Memory isn't."

**The Solution:**
> "RadAssist Pro doesn't just detect—it remembers. It's the first AI that treats a patient's imaging history as a coherent narrative."

### 3. Demo Scenario: "The Missed Progression Save"

**Patient Story:**
- 58-year-old former smoker
- Incidental 6mm lung nodule found 18 months ago
- Four follow-up CTs since then
- Traditional read: "Stable nodule, continued surveillance"
- **RadAssist Pro:** "2.3mm growth over 18 months (38% volume increase), growth rate consistent with malignancy, recommend tissue sampling"

### 4. Positioning Against Commercial Products

| Commercial Weakness | Your Hackathon Angle |
|---------------------|----------------------|
| Black box outputs | Show MedGemma's reasoning chain |
| Require expensive integration | Demo works on uploaded DICOM pairs |
| Focus on detection, not communication | Generate patient-friendly summaries |
| Trained on narrow datasets | Show generalization across modalities |

### 5. Open Source Framing

**Don't say:** "It's free and anyone can use it"
**Do say:** "We're building the standard for longitudinal medical AI"

Three pillars:
1. **Trust Through Transparency** - Clinicians need to see how decisions are made
2. **Community-Driven Validation** - Distributed peer review
3. **Infrastructure, Not Product** - The foundation for future medical AI

### 6. Demo Video Structure (8 minutes)

| Time | Section | Content |
|------|---------|---------|
| 0:00-0:30 | Hook | Patient story: told "stable" four times |
| 0:30-1:30 | Problem | Longitudinal comparison is manual |
| 1:30-2:30 | Insight | Detection solved; comparison isn't |
| 2:30-5:30 | **Demo** | Core functionality walkthrough |
| 5:30-6:30 | Technology | MedGemma architecture, temporal reasoning |
| 6:30-7:30 | Impact | Time saved, lives saved statistics |
| 7:30-8:00 | Vision | Roadmap, community, call to action |

---

## Messaging Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│  TAGLINE                                                     │
│  "AI That Remembers"                                         │
├──────────────────────────────────────────────────────────────┤
│  VALUE PROPOSITION                                           │
│  "The first open-source AI that automatically detects,       │
│  quantifies, and summarizes changes between sequential       │
│  medical images—turning complex comparisons into clear,      │
│  actionable insights."                                       │
├──────────────────────────────────────────────────────────────┤
│  PROOF POINTS                                                │
│  • Quantified change detection (not just "stable/changed")   │
│  • Risk stratification with clinical guidelines              │
│  • Natural language report generation                        │
│  • Open source for transparency and trust                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Competitive Differentiation Matrix

```
                        PROPRIETARY              OPEN SOURCE
                    ┌─────────────────────┬─────────────────────┐
                    │                     │                     │
    SINGLE-IMAGE    │   Most Competitors  │   Some Research     │
    DETECTION       │   (Commoditized)    │   Projects          │
                    │                     │                     │
                    ├─────────────────────┼─────────────────────┤
                    │                     │                     │
    LONGITUDINAL    │   Limited/None      │   RadAssist Pro     │
    WITH CLINICAL   │   (Too Complex)     │   ★ YOU ARE HERE    │
    DECISION SUPPORT│                     │                     │
                    └─────────────────────┴─────────────────────┘
```

---

## Updated Feature Prioritization

### MVP (Days 11-17) - REVISED

1. **Longitudinal Comparison Core**
   - Upload two CT scans from different dates
   - Automatic nodule identification and correspondence
   - Quantified change measurement (mm, %, volume)
   - Natural language change summary

2. **Clinical Decision Support**
   - Volume doubling time calculation
   - Lung-RADS category assignment
   - Differential diagnosis evolution
   - Suggested follow-up actions

3. **Report Generation**
   - Draft comparison paragraph for reports
   - Structured findings output
   - Patient-friendly summary option

### Target (Days 18-25)

4. **Multi-timepoint Support**
   - 3+ studies timeline
   - Trend visualization
   - Progression/stability tracking

5. **Demo Polish**
   - Clean UI for video capture
   - Example cases library
   - Export capabilities

### Stretch (Deprioritized)

6. **3D Volumetric Rendering** - Only if core is solid
7. **Other modalities** - CT only for now
8. **Patient portal** - Radiologist-focused first

---

## Anticipated Judge Questions

| Question | Answer |
|----------|--------|
| "How different from PACS comparison?" | "PACS shows images. We analyze them—quantifying change, risk stratification, generating reports." |
| "What's your validation data?" | "[Dataset] with [results]. Open source enables continuous community validation." |
| "Regulatory pathway?" | "Clinical decision support, not autonomous diagnosis. Open source accelerates regulatory through transparency." |
| "Why should Google care?" | "MedGemma was built for complex, multimodal, clinically meaningful problems. This is exactly that." |

---

## Action Items

### Immediate (Days 9-10)

1. [ ] **Test MedGemma on paired scans** - Can it identify corresponding anatomy?
2. [ ] **Talk to 2-3 radiologists** - Validate workflow pain point
3. [ ] **Update PROJECT_PROPOSAL.md** with narrow focus
4. [ ] **Create demo storyboard** following video structure

### Week 2 (Days 11-17)

1. [ ] Build core longitudinal comparison
2. [ ] Add clinical decision support (Lung-RADS)
3. [ ] Implement report generation
4. [ ] Validate with synthetic longitudinal cases

### Week 3-4 (Days 18-32)

1. [ ] Polish UI for demo
2. [ ] Record demo video
3. [ ] Create presentation materials
4. [ ] Final testing

---

## Final Strategic Position

**From:** "RadAssist Pro - AI Radiology Assistant with 3D & Longitudinal"

**To:** "RadAssist Pro - AI That Remembers"

**Core Innovation:** Automated longitudinal change detection with clinical decision support

**Why We Win:**
1. Novel problem space (not detection - change tracking)
2. MedGemma's temporal reasoning is uniquely suited
3. Open source provides transparency edge
4. Clinical workflow integration (report generation)
5. Complete solution (measurement + risk + recommendation)

**Closing Statement:**
> "You're not building another detection tool. You're building the memory layer for medical AI."

---

**Document Version:** 1.0
**Last Updated:** January 21, 2026
