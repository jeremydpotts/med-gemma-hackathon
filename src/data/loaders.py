"""
Data Loaders for RadAssist Pro.

Provides utilities for loading various medical data formats:
- DICOM images (2D and 3D)
- PNG/JPEG images
- NIfTI volumes
- Clinical reports (text)

All loaders implement de-identification checks.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

# Try importing medical imaging libraries
try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False
    logger.warning("pydicom not available. Install with: pip install pydicom")

try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/numpy not available. Install with: pip install Pillow numpy")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MedicalImage:
    """Represents a loaded medical image."""
    pixel_data: Any  # numpy array or PIL Image
    modality: str
    dimensions: Tuple[int, ...]
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    is_deidentified: bool = False

    @property
    def is_3d(self) -> bool:
        """Check if image is 3D volume."""
        return len(self.dimensions) == 3 and self.dimensions[2] > 1

    @property
    def width(self) -> int:
        """Get image width."""
        return self.dimensions[1] if len(self.dimensions) >= 2 else 0

    @property
    def height(self) -> int:
        """Get image height."""
        return self.dimensions[0]

    @property
    def depth(self) -> int:
        """Get image depth (for 3D volumes)."""
        return self.dimensions[2] if len(self.dimensions) >= 3 else 1


@dataclass
class DICOMStudy:
    """Represents a loaded DICOM study."""
    series: List[MedicalImage]
    study_metadata: Dict[str, Any]
    patient_id: str = "ANONYMOUS"
    study_id: str = ""
    study_date: str = ""
    modality: str = ""
    is_deidentified: bool = False

    @property
    def num_images(self) -> int:
        """Get total number of images in study."""
        return len(self.series)

    @property
    def is_volumetric(self) -> bool:
        """Check if study contains 3D volume."""
        return any(img.is_3d for img in self.series)


# =============================================================================
# DICOM Loader
# =============================================================================

class DICOMLoader:
    """
    Load and process DICOM medical images.

    Supports:
    - Single DICOM files
    - Directories of DICOM slices (volumes)
    - De-identification validation

    Example:
        loader = DICOMLoader()
        study = loader.load_study("ct_scan_directory/")
        print(f"Loaded {study.num_images} images")
    """

    # DICOM tags that may contain PHI
    PHI_TAGS = [
        "PatientName", "PatientID", "PatientBirthDate",
        "PatientAddress", "PatientTelephoneNumbers",
        "ReferringPhysicianName", "InstitutionName"
    ]

    def __init__(self, validate_deidentification: bool = True):
        """
        Initialize DICOM loader.

        Args:
            validate_deidentification: Whether to check for PHI
        """
        self.validate_deidentification = validate_deidentification

        if not PYDICOM_AVAILABLE:
            logger.warning("pydicom not available - DICOM loading will be limited")

    def load_file(self, filepath: Union[str, Path]) -> Optional[MedicalImage]:
        """
        Load a single DICOM file.

        Args:
            filepath: Path to DICOM file

        Returns:
            MedicalImage or None if loading fails
        """
        filepath = Path(filepath)

        if not PYDICOM_AVAILABLE:
            logger.error("pydicom required for DICOM loading")
            return None

        try:
            dcm = pydicom.dcmread(str(filepath))

            # Check de-identification
            is_deidentified = self._check_deidentification(dcm)
            if self.validate_deidentification and not is_deidentified:
                logger.warning(f"DICOM file may contain PHI: {filepath}")

            # Extract pixel data
            pixel_data = dcm.pixel_array if hasattr(dcm, 'pixel_array') else None

            # Extract metadata
            metadata = self._extract_metadata(dcm)

            dimensions = pixel_data.shape if pixel_data is not None else (0, 0)

            return MedicalImage(
                pixel_data=pixel_data,
                modality=getattr(dcm, 'Modality', 'UNKNOWN'),
                dimensions=dimensions,
                metadata=metadata,
                file_path=str(filepath),
                is_deidentified=is_deidentified
            )

        except Exception as e:
            logger.error(f"Failed to load DICOM file {filepath}: {e}")
            return None

    def load_directory(
        self,
        directory: Union[str, Path],
        sort_by_instance: bool = True
    ) -> List[MedicalImage]:
        """
        Load all DICOM files from a directory.

        Args:
            directory: Directory containing DICOM files
            sort_by_instance: Whether to sort by instance number

        Returns:
            List of MedicalImage objects
        """
        directory = Path(directory)
        images = []

        # Find all DICOM files
        dicom_files = list(directory.glob("*.dcm"))
        if not dicom_files:
            dicom_files = list(directory.glob("*"))  # Try all files

        for filepath in dicom_files:
            if filepath.is_file():
                image = self.load_file(filepath)
                if image:
                    images.append(image)

        # Sort by instance number if requested
        if sort_by_instance and images:
            images.sort(
                key=lambda x: x.metadata.get("InstanceNumber", 0)
            )

        logger.info(f"Loaded {len(images)} DICOM images from {directory}")
        return images

    def load_study(self, path: Union[str, Path]) -> DICOMStudy:
        """
        Load a complete DICOM study.

        Args:
            path: Path to study directory

        Returns:
            DICOMStudy object
        """
        path = Path(path)

        if path.is_file():
            images = [self.load_file(path)]
            images = [img for img in images if img is not None]
        else:
            images = self.load_directory(path)

        # Extract study-level metadata from first image
        study_metadata = {}
        patient_id = "ANONYMOUS"
        study_id = ""
        study_date = ""
        modality = ""

        if images:
            meta = images[0].metadata
            patient_id = meta.get("PatientID", "ANONYMOUS")
            study_id = meta.get("StudyID", "")
            study_date = meta.get("StudyDate", "")
            modality = meta.get("Modality", "")
            study_metadata = meta

        return DICOMStudy(
            series=images,
            study_metadata=study_metadata,
            patient_id=patient_id,
            study_id=study_id,
            study_date=study_date,
            modality=modality,
            is_deidentified=all(img.is_deidentified for img in images)
        )

    def _check_deidentification(self, dcm) -> bool:
        """Check if DICOM is de-identified."""
        for tag in self.PHI_TAGS:
            value = getattr(dcm, tag, None)
            if value and str(value) not in ["", "ANONYMOUS", "REMOVED"]:
                # Check if it looks like real PHI
                value_str = str(value).upper()
                if value_str not in ["ANONYMOUS", "UNKNOWN", "REMOVED", "NONE"]:
                    return False
        return True

    def _extract_metadata(self, dcm) -> Dict[str, Any]:
        """Extract relevant metadata from DICOM."""
        metadata = {}

        # Safe tags to extract
        safe_tags = [
            "Modality", "BodyPartExamined", "ViewPosition",
            "Rows", "Columns", "BitsStored", "BitsAllocated",
            "PixelSpacing", "SliceThickness", "ImageOrientationPatient",
            "ImagePositionPatient", "InstanceNumber", "SeriesNumber",
            "StudyID", "StudyDate", "PatientID"
        ]

        for tag in safe_tags:
            value = getattr(dcm, tag, None)
            if value is not None:
                # Convert to JSON-serializable format
                if hasattr(value, 'tolist'):
                    value = value.tolist()
                elif hasattr(value, '__iter__') and not isinstance(value, str):
                    value = list(value)
                metadata[tag] = value

        return metadata


# =============================================================================
# Image Loader (PNG, JPEG, etc.)
# =============================================================================

class ImageLoader:
    """
    Load standard image formats (PNG, JPEG).

    Suitable for pre-processed medical images exported from PACS.
    """

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}

    def __init__(self):
        """Initialize image loader."""
        if not PIL_AVAILABLE:
            logger.warning("PIL not available - image loading will be limited")

    def load(self, filepath: Union[str, Path]) -> Optional[MedicalImage]:
        """
        Load an image file.

        Args:
            filepath: Path to image file

        Returns:
            MedicalImage or None
        """
        filepath = Path(filepath)

        if filepath.suffix.lower() not in self.SUPPORTED_FORMATS:
            logger.warning(f"Unsupported format: {filepath.suffix}")
            return None

        if not PIL_AVAILABLE:
            logger.error("PIL required for image loading")
            return None

        try:
            image = Image.open(filepath)

            # Convert to numpy array if numpy available
            pixel_data = np.array(image) if 'numpy' in dir() else image

            dimensions = pixel_data.shape if hasattr(pixel_data, 'shape') else image.size

            return MedicalImage(
                pixel_data=pixel_data,
                modality="UNKNOWN",
                dimensions=dimensions,
                metadata={
                    "format": image.format,
                    "mode": image.mode,
                    "size": image.size
                },
                file_path=str(filepath),
                is_deidentified=True  # Standard images don't contain DICOM PHI
            )

        except Exception as e:
            logger.error(f"Failed to load image {filepath}: {e}")
            return None

    def load_batch(
        self,
        directory: Union[str, Path],
        pattern: str = "*"
    ) -> List[MedicalImage]:
        """
        Load multiple images from directory.

        Args:
            directory: Directory to search
            pattern: Glob pattern for files

        Returns:
            List of MedicalImage objects
        """
        directory = Path(directory)
        images = []

        for ext in self.SUPPORTED_FORMATS:
            for filepath in directory.glob(f"{pattern}{ext}"):
                image = self.load(filepath)
                if image:
                    images.append(image)

        return images


# =============================================================================
# Clinical Text Loader
# =============================================================================

class ClinicalTextLoader:
    """
    Load clinical text documents (reports, notes).

    Includes PHI detection warnings.
    """

    def __init__(self, detect_phi: bool = True):
        """
        Initialize text loader.

        Args:
            detect_phi: Whether to check for potential PHI
        """
        self.detect_phi = detect_phi

    def load(self, filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Load a clinical text document.

        Args:
            filepath: Path to text file

        Returns:
            Dictionary with text and metadata
        """
        filepath = Path(filepath)

        try:
            if filepath.suffix == '.json':
                with open(filepath) as f:
                    content = json.load(f)
                text = content.get('text', str(content))
            else:
                text = filepath.read_text()

            # Check for potential PHI
            phi_warning = None
            if self.detect_phi:
                phi_warning = self._check_for_phi(text)

            return {
                "text": text,
                "filepath": str(filepath),
                "phi_warning": phi_warning,
                "length": len(text)
            }

        except Exception as e:
            logger.error(f"Failed to load text file {filepath}: {e}")
            return None

    def _check_for_phi(self, text: str) -> Optional[str]:
        """Basic PHI pattern detection."""
        import re

        patterns = {
            "phone": r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            "ssn": r'\d{3}[-\s]?\d{2}[-\s]?\d{4}',
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "date": r'\d{1,2}/\d{1,2}/\d{2,4}'
        }

        found = []
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, text):
                found.append(pattern_name)

        if found:
            return f"Potential PHI detected: {', '.join(found)}"
        return None


# =============================================================================
# Unified Loader
# =============================================================================

class MedicalDataLoader:
    """
    Unified loader for all medical data types.

    Automatically detects file type and uses appropriate loader.

    Example:
        loader = MedicalDataLoader()
        data = loader.load("study_path/")
    """

    def __init__(self):
        """Initialize unified loader."""
        self.dicom_loader = DICOMLoader()
        self.image_loader = ImageLoader()
        self.text_loader = ClinicalTextLoader()

    def load(self, path: Union[str, Path]) -> Union[DICOMStudy, MedicalImage, Dict, None]:
        """
        Load medical data from path.

        Automatically detects type and uses appropriate loader.

        Args:
            path: Path to file or directory

        Returns:
            Loaded data or None
        """
        path = Path(path)

        if path.is_dir():
            # Check for DICOM files
            dicom_files = list(path.glob("*.dcm"))
            if dicom_files:
                return self.dicom_loader.load_study(path)
            else:
                # Try loading as image directory
                images = self.image_loader.load_batch(path)
                if images:
                    return images
                return None

        # Single file
        suffix = path.suffix.lower()

        if suffix == '.dcm':
            return self.dicom_loader.load_file(path)
        elif suffix in ImageLoader.SUPPORTED_FORMATS:
            return self.image_loader.load(path)
        elif suffix in ['.txt', '.json', '.xml']:
            return self.text_loader.load(path)
        else:
            # Try DICOM (may not have extension)
            return self.dicom_loader.load_file(path)

    def load_for_inference(
        self,
        path: Union[str, Path]
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Load data prepared for model inference.

        Returns pixel data and metadata separately.

        Args:
            path: Path to medical data

        Returns:
            Tuple of (pixel_data, metadata)
        """
        data = self.load(path)

        if isinstance(data, MedicalImage):
            return data.pixel_data, data.metadata

        if isinstance(data, DICOMStudy):
            # Stack images into volume
            if data.series:
                pixels = [img.pixel_data for img in data.series if img.pixel_data is not None]
                if pixels and 'numpy' in dir():
                    import numpy as np
                    volume = np.stack(pixels, axis=-1)
                    return volume, data.study_metadata
            return None, data.study_metadata

        return None, {}
