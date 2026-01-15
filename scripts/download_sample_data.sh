#!/bin/bash
# Download Sample Medical Datasets for MedGemma Testing
# Med-Gemma Impact Challenge - Phase 1

set -e

echo "=========================================="
echo "Downloading Sample Medical Datasets"
echo "Med-Gemma Impact Challenge"
echo "=========================================="
echo ""

# Create directories
mkdir -p ../data/raw/chest_xray
mkdir -p ../data/raw/clinical_text
mkdir -p ../data/raw/sample_ct_mri
mkdir -p ../data/processed

# Note: For this hackathon, we'll focus on publicly available sample data
# that demonstrates MedGemma capabilities without requiring large downloads

echo "Step 1: Downloading sample chest X-ray images..."
echo "Note: Using small subset for initial testing"
echo ""

# For now, we'll document the datasets we plan to use
# Actual downloads would require more storage and time

cat > ../data/raw/DATA_SOURCES.md << 'EOF'
# Medical Data Sources for MedGemma Testing

## Datasets Identified for Use

### 1. NIH Chest X-ray Dataset
- **Source:** https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community
- **Size:** 112,120 frontal-view X-ray images
- **Format:** PNG
- **Labels:** Disease labels from NLP on radiology reports
- **Use Case:** Testing MedGemma's 2D medical imaging interpretation
- **Status:** Available via Kaggle or direct download

### 2. Sample CT Scans
- **Source:** Cancer Imaging Archive (TCIA)
- **Format:** DICOM
- **Use Case:** Testing MedGemma 1.5's 3D imaging capabilities
- **Status:** Requires registration and specific collection selection

### 3. MIMIC-CXR Demo
- **Source:** PhysioNet (requires credentialing)
- **Content:** Chest X-rays with radiology reports
- **Use Case:** Multimodal testing (image + text)
- **Status:** Requires PhysioNet credentialing

### 4. Medical Image Samples
- **Source:** Public medical image repositories
- **Use Case:** Quick testing and prototyping
- **Status:** Can use CC-licensed medical images

## Implementation Strategy

For this hackathon, we will:

1. **Use small sample datasets** for initial MedGemma testing
2. **Focus on demonstrating capabilities** rather than large-scale training
3. **Create synthetic test cases** using MedGemma itself if needed
4. **Prioritize quality over quantity** for demo purposes

## Next Steps

1. Download representative samples (not full datasets)
2. Test MedGemma on diverse medical data types
3. Document performance and capabilities
4. Use findings to inform tool selection in brainstorming phase
EOF

echo "✓ Dataset documentation created"
echo ""

echo "Step 2: Creating sample medical text data..."

# Create sample clinical scenarios for testing
cat > ../data/raw/clinical_text/sample_cases.json << 'EOF'
{
  "cases": [
    {
      "id": "case_001",
      "type": "chest_pain",
      "patient": {
        "age": 65,
        "sex": "M",
        "history": ["hypertension", "diabetes", "hyperlipidemia"]
      },
      "presentation": "65-year-old male with substernal chest pain for 2 hours, radiating to left arm. Associated with shortness of breath and diaphoresis.",
      "vitals": {
        "BP": "160/95",
        "HR": 105,
        "RR": 22,
        "SpO2": "89% on room air",
        "Temp": "37.2°C"
      },
      "labs": {
        "troponin": "0.8 ng/mL (elevated)",
        "BNP": "450 pg/mL",
        "CK-MB": "elevated"
      },
      "question": "What is the most likely diagnosis and recommended immediate management?"
    },
    {
      "id": "case_002",
      "type": "respiratory",
      "patient": {
        "age": 45,
        "sex": "F",
        "history": ["asthma", "seasonal allergies"]
      },
      "presentation": "Worsening dyspnea over 3 days, productive cough with green sputum, fever to 101°F.",
      "vitals": {
        "BP": "125/80",
        "HR": 98,
        "RR": 24,
        "SpO2": "91% on room air",
        "Temp": "38.3°C"
      },
      "labs": {
        "WBC": "15,000/μL with left shift",
        "CRP": "12 mg/dL",
        "procalcitonin": "0.8 ng/mL"
      },
      "imaging": "Chest X-ray shows right lower lobe consolidation",
      "question": "Interpret the findings and recommend treatment."
    },
    {
      "id": "case_003",
      "type": "oncology",
      "patient": {
        "age": 58,
        "sex": "M",
        "history": ["40 pack-year smoking history"]
      },
      "presentation": "Persistent cough for 8 weeks, unintentional 15 lb weight loss, hemoptysis.",
      "vitals": {
        "BP": "130/85",
        "HR": 88,
        "RR": 18,
        "SpO2": "94% on room air"
      },
      "imaging": "CT chest shows 3.2 cm spiculated mass in right upper lobe with hilar lymphadenopathy",
      "question": "Describe findings, differential diagnosis, and recommended next steps."
    }
  ]
}
EOF

echo "✓ Sample clinical cases created"
echo ""

echo "Step 3: Setting up data exploration structure..."

# Create README for processed data
cat > ../data/processed/README.md << 'EOF'
# Processed Data Directory

This directory contains processed and cleaned medical data ready for MedGemma testing and application development.

## Processing Pipeline

1. **Download** raw data from public sources
2. **Validate** data formats and quality
3. **Preprocess** for MedGemma input (resize, normalize, format)
4. **Organize** by use case and modality
5. **Document** processing steps and metadata

## Subdirectories

- `chest_xray/` - Preprocessed chest X-ray images
- `ct_scans/` - 3D CT volumes in compatible format
- `mri_scans/` - MRI volumes
- `clinical_text/` - Structured clinical text data
- `multimodal/` - Combined image + text datasets

## Data Format Standards

- **Images:** PNG or JPEG (2D), NIfTI or DICOM (3D)
- **Text:** JSON or structured markdown
- **Metadata:** JSON with standardized schema
- **Labels:** Consistent labeling scheme across datasets
EOF

echo "✓ Processed data structure created"
echo ""

echo "=========================================="
echo "Sample Data Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Review data sources in data/raw/DATA_SOURCES.md"
echo "2. Test MedGemma on sample clinical cases"
echo "3. Document findings and capabilities"
echo "4. Identify datasets needed for final application"
echo ""
echo "For full datasets, use appropriate download tools:"
echo "- Kaggle datasets: kaggle datasets download"
echo "- TCIA: Use TCIA download tools"
echo "- PhysioNet: Requires credentialing"
