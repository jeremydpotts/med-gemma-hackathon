"""
Data Preprocessing for RadAssist Pro.

Provides preprocessing utilities for medical images:
- Normalization
- Resizing
- Windowing (for CT)
- Augmentation
- Format conversion
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

# Try importing numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available. Install with: pip install numpy")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PreprocessingConfig:
    """Configuration for image preprocessing."""
    # Resizing
    target_size: Tuple[int, int] = (512, 512)
    preserve_aspect_ratio: bool = True
    interpolation: str = "bilinear"

    # Normalization
    normalize: bool = True
    normalization_method: str = "minmax"  # minmax, zscore, percentile
    clip_values: Optional[Tuple[float, float]] = None

    # CT Windowing
    apply_windowing: bool = False
    window_center: float = 40.0
    window_width: float = 400.0

    # Data type
    output_dtype: str = "float32"


@dataclass
class PreprocessedImage:
    """Result of preprocessing."""
    data: Any  # numpy array
    original_shape: Tuple[int, ...]
    processed_shape: Tuple[int, ...]
    preprocessing_applied: List[str]
    config: PreprocessingConfig


# =============================================================================
# Preprocessor
# =============================================================================

class ImagePreprocessor:
    """
    Preprocess medical images for model input.

    Example:
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(image_data)
        model_input = result.data
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize preprocessor.

        Args:
            config: Preprocessing configuration
        """
        self.config = config or PreprocessingConfig()

        if not NUMPY_AVAILABLE:
            logger.warning("numpy not available - preprocessing will be limited")

    def preprocess(
        self,
        data: Any,
        config: Optional[PreprocessingConfig] = None
    ) -> PreprocessedImage:
        """
        Preprocess image data for model input.

        Args:
            data: Input image data (numpy array)
            config: Optional override config

        Returns:
            PreprocessedImage with processed data
        """
        config = config or self.config
        steps_applied = []
        original_shape = data.shape if hasattr(data, 'shape') else (0,)

        if not NUMPY_AVAILABLE:
            return PreprocessedImage(
                data=data,
                original_shape=original_shape,
                processed_shape=original_shape,
                preprocessing_applied=["none - numpy not available"],
                config=config
            )

        # Convert to numpy if needed
        if not isinstance(data, np.ndarray):
            data = np.array(data)
            steps_applied.append("to_numpy")

        # Apply CT windowing if configured
        if config.apply_windowing:
            data = self._apply_windowing(
                data,
                config.window_center,
                config.window_width
            )
            steps_applied.append(f"windowing(c={config.window_center}, w={config.window_width})")

        # Clip values if specified
        if config.clip_values:
            data = np.clip(data, config.clip_values[0], config.clip_values[1])
            steps_applied.append(f"clip{config.clip_values}")

        # Normalize
        if config.normalize:
            data = self._normalize(data, config.normalization_method)
            steps_applied.append(f"normalize({config.normalization_method})")

        # Resize
        if config.target_size:
            data = self._resize(
                data,
                config.target_size,
                config.preserve_aspect_ratio,
                config.interpolation
            )
            steps_applied.append(f"resize{config.target_size}")

        # Convert data type
        data = data.astype(config.output_dtype)
        steps_applied.append(f"dtype({config.output_dtype})")

        return PreprocessedImage(
            data=data,
            original_shape=original_shape,
            processed_shape=data.shape,
            preprocessing_applied=steps_applied,
            config=config
        )

    def preprocess_batch(
        self,
        images: List[Any],
        config: Optional[PreprocessingConfig] = None
    ) -> List[PreprocessedImage]:
        """
        Preprocess multiple images.

        Args:
            images: List of image data
            config: Optional override config

        Returns:
            List of PreprocessedImage objects
        """
        return [self.preprocess(img, config) for img in images]

    def _apply_windowing(
        self,
        data: np.ndarray,
        center: float,
        width: float
    ) -> np.ndarray:
        """
        Apply CT windowing.

        Converts Hounsfield units to displayable range.

        Args:
            data: CT data in HU
            center: Window center
            width: Window width

        Returns:
            Windowed data
        """
        lower = center - width / 2
        upper = center + width / 2

        windowed = np.clip(data, lower, upper)
        windowed = (windowed - lower) / (upper - lower)

        return windowed

    def _normalize(
        self,
        data: np.ndarray,
        method: str = "minmax"
    ) -> np.ndarray:
        """
        Normalize image data.

        Args:
            data: Image data
            method: Normalization method (minmax, zscore, percentile)

        Returns:
            Normalized data
        """
        if method == "minmax":
            min_val = data.min()
            max_val = data.max()
            if max_val > min_val:
                return (data - min_val) / (max_val - min_val)
            return data

        elif method == "zscore":
            mean = data.mean()
            std = data.std()
            if std > 0:
                return (data - mean) / std
            return data - mean

        elif method == "percentile":
            p1 = np.percentile(data, 1)
            p99 = np.percentile(data, 99)
            data = np.clip(data, p1, p99)
            if p99 > p1:
                return (data - p1) / (p99 - p1)
            return data

        else:
            logger.warning(f"Unknown normalization method: {method}")
            return data

    def _resize(
        self,
        data: np.ndarray,
        target_size: Tuple[int, int],
        preserve_aspect_ratio: bool,
        interpolation: str
    ) -> np.ndarray:
        """
        Resize image data.

        Args:
            data: Image data
            target_size: Target (height, width)
            preserve_aspect_ratio: Whether to preserve aspect ratio
            interpolation: Interpolation method

        Returns:
            Resized data
        """
        # For 2D images
        if len(data.shape) == 2:
            return self._resize_2d(data, target_size, preserve_aspect_ratio)

        # For 3D volumes, resize each slice
        elif len(data.shape) == 3:
            slices = []
            for i in range(data.shape[2]):
                resized_slice = self._resize_2d(
                    data[:, :, i],
                    target_size,
                    preserve_aspect_ratio
                )
                slices.append(resized_slice)
            return np.stack(slices, axis=2)

        return data

    def _resize_2d(
        self,
        data: np.ndarray,
        target_size: Tuple[int, int],
        preserve_aspect_ratio: bool
    ) -> np.ndarray:
        """
        Simple 2D resize using numpy.

        For production, would use scipy.ndimage or PIL.
        """
        current_h, current_w = data.shape[:2]
        target_h, target_w = target_size

        if preserve_aspect_ratio:
            # Calculate scaling to fit within target while preserving ratio
            scale = min(target_h / current_h, target_w / current_w)
            new_h = int(current_h * scale)
            new_w = int(current_w * scale)
        else:
            new_h, new_w = target_h, target_w

        # Simple nearest-neighbor resize
        # In production, use scipy.ndimage.zoom or cv2.resize
        row_indices = (np.arange(new_h) * current_h / new_h).astype(int)
        col_indices = (np.arange(new_w) * current_w / new_w).astype(int)

        resized = data[row_indices][:, col_indices]

        # Pad if preserving aspect ratio
        if preserve_aspect_ratio:
            padded = np.zeros((target_h, target_w), dtype=data.dtype)
            pad_h = (target_h - new_h) // 2
            pad_w = (target_w - new_w) // 2
            padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
            return padded

        return resized


# =============================================================================
# CT-Specific Preprocessing
# =============================================================================

class CTPreprocessor(ImagePreprocessor):
    """
    CT-specific preprocessing with common window presets.
    """

    # Common CT window presets
    WINDOW_PRESETS = {
        "lung": {"center": -600, "width": 1500},
        "mediastinum": {"center": 40, "width": 400},
        "bone": {"center": 400, "width": 2000},
        "brain": {"center": 40, "width": 80},
        "liver": {"center": 60, "width": 160},
        "soft_tissue": {"center": 40, "width": 350}
    }

    def __init__(self, window_preset: str = "lung"):
        """
        Initialize CT preprocessor with window preset.

        Args:
            window_preset: Name of window preset
        """
        preset = self.WINDOW_PRESETS.get(window_preset, self.WINDOW_PRESETS["lung"])

        config = PreprocessingConfig(
            apply_windowing=True,
            window_center=preset["center"],
            window_width=preset["width"]
        )

        super().__init__(config)
        self.preset_name = window_preset

    def preprocess_volume(
        self,
        volume: np.ndarray,
        window_presets: Optional[List[str]] = None
    ) -> Dict[str, PreprocessedImage]:
        """
        Preprocess CT volume with multiple window presets.

        Args:
            volume: CT volume data
            window_presets: List of preset names to apply

        Returns:
            Dictionary of windowed volumes by preset name
        """
        if window_presets is None:
            window_presets = ["lung", "mediastinum", "bone"]

        results = {}

        for preset_name in window_presets:
            preset = self.WINDOW_PRESETS.get(preset_name)
            if preset:
                config = PreprocessingConfig(
                    apply_windowing=True,
                    window_center=preset["center"],
                    window_width=preset["width"]
                )
                results[preset_name] = self.preprocess(volume, config)

        return results


# =============================================================================
# Utility Functions
# =============================================================================

def quick_preprocess(
    data: Any,
    target_size: Tuple[int, int] = (512, 512),
    normalize: bool = True
) -> np.ndarray:
    """
    Quick preprocessing for common use cases.

    Args:
        data: Image data
        target_size: Target size
        normalize: Whether to normalize

    Returns:
        Preprocessed numpy array
    """
    config = PreprocessingConfig(
        target_size=target_size,
        normalize=normalize
    )

    preprocessor = ImagePreprocessor(config)
    result = preprocessor.preprocess(data)

    return result.data


def prepare_for_model(
    data: Any,
    model_input_size: Tuple[int, int] = (224, 224),
    add_batch_dim: bool = True,
    add_channel_dim: bool = True
) -> np.ndarray:
    """
    Prepare image for model input.

    Args:
        data: Image data
        model_input_size: Required input size for model
        add_batch_dim: Whether to add batch dimension
        add_channel_dim: Whether to add channel dimension

    Returns:
        Model-ready numpy array
    """
    if not NUMPY_AVAILABLE:
        return data

    # Preprocess
    processed = quick_preprocess(data, model_input_size)

    # Add channel dimension if grayscale
    if add_channel_dim and len(processed.shape) == 2:
        processed = processed[..., np.newaxis]

    # Add batch dimension
    if add_batch_dim:
        processed = processed[np.newaxis, ...]

    return processed
