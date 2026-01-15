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
