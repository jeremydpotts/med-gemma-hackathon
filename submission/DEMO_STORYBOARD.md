# RadAssist Pro - Demo Video Storyboard

**Video Length:** 8 minutes
**Target:** Med-Gemma Impact Challenge judges
**Tagline:** "AI That Remembers"

---

## Video Structure Overview

```
┌────────────────────────────────────────────────────────────────────┐
│  0:00-0:30  │  THE HOOK (30 sec)                                   │
├────────────────────────────────────────────────────────────────────┤
│  0:30-1:30  │  THE PROBLEM (60 sec)                                │
├────────────────────────────────────────────────────────────────────┤
│  1:30-2:30  │  THE INSIGHT (60 sec)                                │
├────────────────────────────────────────────────────────────────────┤
│  2:30-5:30  │  THE DEMO (180 sec) ★ Core of video                  │
├────────────────────────────────────────────────────────────────────┤
│  5:30-6:30  │  THE TECHNOLOGY (60 sec)                             │
├────────────────────────────────────────────────────────────────────┤
│  6:30-7:30  │  THE IMPACT (60 sec)                                 │
├────────────────────────────────────────────────────────────────────┤
│  7:30-8:00  │  THE VISION (30 sec)                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## Scene 1: THE HOOK (0:00-0:30)

### Visual
- Fade in on a CT scan image
- Text overlay: "A patient was told 'stable' four times."
- Pause
- Text overlay changes: "She had cancer."
- Cut to RadAssist Pro logo

### Script
> "A 58-year-old woman had four follow-up CT scans over 18 months. Each time, the report said 'stable nodule, continued surveillance.' But the nodule wasn't stable—it was growing. By the time anyone noticed, it was Stage 2 lung cancer."
>
> "This is the problem RadAssist Pro was built to solve."

### Notes
- Emotional, not technical
- Creates immediate stakes
- 30 seconds max

---

## Scene 2: THE PROBLEM (0:30-1:30)

### Visual
- Split screen: radiologist workstation / timer counting
- Statistics appearing on screen
- Overwhelmed radiologist metaphor (stack of studies)

### Script
> "Radiologists aren't failing at detection—they're drowning in comparison."
>
> "The average radiologist reads 50 or more studies every day. For each one with a prior exam, they spend 15 to 20 minutes manually scrolling between scans, trying to spot subtle changes."
>
> "That's 15 minutes times 30 comparison cases times 250 working days. The math doesn't work."
>
> "And when the math doesn't work, subtle progression gets missed. Patients fall through the cracks."

### On-Screen Stats
- "42+ FDA-approved detection tools"
- "But detection is solved"
- "Comparison isn't"
- "15+ min per comparison"
- "3-5% of significant changes missed"

### Notes
- Establish the pain point
- Show this is a workflow problem, not a detection problem
- 60 seconds

---

## Scene 3: THE INSIGHT (1:30-2:30)

### Visual
- Side-by-side comparison: "Detection" vs "Memory"
- MedGemma 1.5 capabilities highlight
- Timeline visualization

### Script
> "Here's what we realized: AI has gotten incredibly good at detecting findings on a single image. But detecting change across time—that requires memory."
>
> "MedGemma 1.5, the model we're using, has a unique capability: it can analyze sequential medical images and understand what changed between them. It doesn't just see snapshots—it sees the story."
>
> "RadAssist Pro is the first open-source application that harnesses this capability. We turn complex longitudinal comparisons into clear, actionable insights."

### Key Points
- Detection = solved (commoditized)
- Memory/Comparison = unsolved (our opportunity)
- MedGemma 1.5 uniquely enables this
- Open source for transparency and trust

### Notes
- Bridge from problem to solution
- Establish MedGemma connection
- 60 seconds

---

## Scene 4: THE DEMO (2:30-5:30) ★ CORE

### Structure (3 minutes total)

**Part A: Upload & Alignment (30 sec)**

Visual: Screen recording of RadAssist Pro interface

> "Let me show you how it works. I'm uploading four CT scans from the same patient, taken over 18 months."

- Show clean Streamlit interface
- Upload 4 DICOM studies
- Show automatic alignment/registration

**Part B: Change Detection (60 sec)**

Visual: Side-by-side scans with highlighting

> "RadAssist Pro automatically identifies the nodule in the right upper lobe and tracks it across all four timepoints. Watch what happens."

- Show nodule identification
- Display measurements: 6mm → 6.2mm → 6.8mm → 8.3mm
- Highlight the change visually
- Show confidence scores

**Part C: Clinical Decision Support (60 sec)**

Visual: The generated analysis

> "Here's where RadAssist Pro goes beyond simple measurement. It calculates volume doubling time, applies Lung-RADS guidelines, and shows how the differential diagnosis should evolve."

Display the output:
```
LONGITUDINAL ANALYSIS: Right upper lobe nodule

Timeline:
- 2024-01-15: 6mm solid nodule (Lung-RADS 4A)
- 2024-07-20: 6.2mm (+3%)
- 2025-01-18: 6.8mm (+10%)
- 2025-07-15: 8.3mm (+38% total)

Volume Doubling Time: ~320 days

Risk Assessment: ELEVATED
Volume doubling time <400 days associated with
increased malignancy probability.

Updated Differential:
1. Primary lung malignancy - INCREASED from baseline
2. Inflammatory/infectious - DECREASED (would expect resolution)
3. Slow-growing carcinoid - STABLE

Recommendation: Per Lung-RADS 4B guidelines,
consider PET-CT or tissue sampling.
```

**Part D: Report Generation (30 sec)**

Visual: Generated report text

> "Finally, RadAssist Pro generates draft language for the radiology report, saving the radiologist from typing the same comparison phrases over and over."

Show:
```
COMPARISON: CT Chest dated 2024-01-15

The previously identified 6mm solid nodule in the right
upper lobe has demonstrated interval growth, now measuring
8.3mm (previously 6mm, 38% increase over 18 months).
Volume doubling time is approximately 320 days, which
raises concern for malignancy. Recommend PET-CT or
tissue sampling per Lung-RADS 4B guidelines.
```

**Part E: The Catch (30 sec)**

Visual: Highlight the key insight

> "Remember our patient who was told 'stable' four times? RadAssist Pro would have flagged this growth pattern by the second scan. Early detection means treatment options. Treatment options mean lives saved."

- Emphasize the clinical impact
- Return to the emotional hook
- Show what could have been caught

### Notes
- This is the heart of the demo
- Show real functionality, not mockups
- Keep narration clear and paced
- 180 seconds total

---

## Scene 5: THE TECHNOLOGY (5:30-6:30)

### Visual
- Architecture diagram
- MedGemma logo
- Code snippets (brief)
- Open source GitHub page

### Script
> "Under the hood, RadAssist Pro is built on Google's MedGemma 1.5, one of the most capable open medical AI models available. We use its multimodal reasoning to analyze sequential images and generate clinically grounded insights."
>
> "Our architecture is designed for real-world deployment: HIPAA-compliant data handling, FHIR-compatible output, and comprehensive test coverage."
>
> "And it's completely open source. In healthcare AI, transparency isn't optional—it's essential for clinical trust. Every line of code is available for review."

### On-Screen Elements
- MedGemma 1.5 architecture (simplified)
- "119 tests passing"
- "HIPAA compliant"
- "FHIR compatible"
- GitHub stars/link

### Notes
- Technical credibility without overwhelming
- Emphasize open source as strength
- 60 seconds

---

## Scene 6: THE IMPACT (6:30-7:30)

### Visual
- Statistics animation
- Testimonial snippet (if available)
- Impact projection

### Script
> "What could this mean for healthcare?"
>
> "If RadAssist Pro saves just 10 minutes per comparison case, that's over 1,000 hours per radiologist per year recovered for patient care."
>
> "If it catches even 1% more progression cases that would have been missed, that's thousands of patients getting treatment earlier."
>
> "And because it's open source, any hospital, any clinic, anywhere in the world can use it. No licensing fees. No vendor lock-in. Just better patient care."

### Statistics to Display
- "15 min saved → 1,000+ hours/year/radiologist"
- "1% more catches → thousands of earlier diagnoses"
- "Open source → global accessibility"
- "Lung cancer 5-year survival: 60% if caught early vs 6% if caught late"

### Notes
- Quantify the impact
- Global/democratization angle
- Connect back to patient outcomes
- 60 seconds

---

## Scene 7: THE VISION (7:30-8:00)

### Visual
- Roadmap preview
- Community/contribution message
- Final tagline

### Script
> "This is just the beginning. Our roadmap includes support for more imaging modalities, integration with major PACS systems, and a growing library of clinical decision support for different conditions."
>
> "We're building this in the open because we believe the future of medical AI should be collaborative, transparent, and accessible to everyone."
>
> "RadAssist Pro. AI that remembers."

### Final Screen
- RadAssist Pro logo
- "AI That Remembers"
- GitHub link
- Med-Gemma Impact Challenge logo

### Notes
- End on vision, not features
- Call to action (implicit)
- Tagline as final words
- 30 seconds

---

## Production Notes

### Do's
- [ ] Use real (de-identified) or realistic synthetic imaging
- [ ] Show actual working UI, not mockups
- [ ] Include brief radiologist testimonial if possible
- [ ] Use clean, medical aesthetic (whites, blues)
- [ ] End on patient outcome, not technology

### Don'ts
- [ ] Don't start with team introductions
- [ ] Don't use unexplained jargon
- [ ] Don't show code unless relevant
- [ ] Don't make unverifiable claims
- [ ] Don't exceed 8 minutes

### Audio
- Professional voiceover (Jeremy or hired)
- Subtle background music (medical/tech feel)
- Clear audio on demo portions

### Graphics Needed
- RadAssist Pro logo
- MedGemma 1.5 logo (with permission)
- Architecture diagram
- Statistics animations
- Timeline visualization

---

## Demo Data Requirements

### Synthetic Patient Case
- 4 sequential CT scans (6, 12, 18, 24 months)
- Right upper lobe nodule showing growth
- Clean, high-quality images
- Fully de-identified/synthetic

### Alternative if CT Not Available
- 4 sequential chest X-rays
- Similar progression pattern
- Adjust script for X-ray instead of CT

---

## Recording Checklist

- [ ] Script finalized and practiced
- [ ] Demo environment tested
- [ ] Synthetic data loaded
- [ ] Screen recording software ready
- [ ] Backup recording option
- [ ] Graphics/overlays prepared
- [ ] Audio equipment tested
- [ ] Quiet recording environment
- [ ] Multiple takes planned

---

**Document Version:** 1.0
**Created:** January 21, 2026
**For:** Med-Gemma Impact Challenge Submission
