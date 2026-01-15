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
