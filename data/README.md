# Data Directory

This directory contains all data files for the Med-Gemma Impact Challenge project.

## Structure

- `raw/` - Raw competition data downloaded from Kaggle (not committed to git)
- `processed/` - Processed and cleaned data ready for model training/inference

## Data Source

Competition data is downloaded from:
https://www.kaggle.com/competitions/med-gemma-impact-challenge

## Download Instructions

```bash
# Ensure Kaggle API is configured
kaggle competitions download -c med-gemma-impact-challenge

# Extract to data/raw/
unzip med-gemma-impact-challenge.zip -d data/raw/
```

## Data Catalog

See `DATA_CATALOG.md` for detailed inventory of all data files, formats, and descriptions.
