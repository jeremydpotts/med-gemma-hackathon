"""
Visualization utilities for RadAssist Pro.

Provides visualization functions for:
- Medical images
- Analysis results
- Reports and metrics
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try importing visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available. Install with: pip install matplotlib")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BoundingBox:
    """Represents a bounding box annotation."""
    x: int
    y: int
    width: int
    height: int
    label: str
    confidence: float = 1.0
    color: str = "red"


@dataclass
class VisualizationConfig:
    """Configuration for visualizations."""
    figure_size: Tuple[int, int] = (10, 10)
    dpi: int = 100
    cmap: str = "gray"
    show_colorbar: bool = False
    show_title: bool = True
    title_fontsize: int = 14
    annotation_color: str = "red"
    annotation_linewidth: int = 2


# =============================================================================
# Image Visualization
# =============================================================================

class MedicalImageVisualizer:
    """
    Visualize medical images with annotations.

    Example:
        viz = MedicalImageVisualizer()
        fig = viz.show_image(image_data, title="Chest X-ray")
        viz.add_bounding_boxes(fig, boxes)
        viz.save_figure(fig, "output.png")
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize visualizer.

        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()

        if not MATPLOTLIB_AVAILABLE:
            logger.warning("matplotlib not available - visualization will be limited")

    def show_image(
        self,
        image_data: Any,
        title: Optional[str] = None,
        window: Optional[Tuple[float, float]] = None
    ) -> Optional[Any]:
        """
        Display a medical image.

        Args:
            image_data: Image data (numpy array)
            title: Optional title
            window: Optional (center, width) for windowing

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib required for visualization")
            return None

        fig, ax = plt.subplots(1, 1, figsize=self.config.figure_size)

        # Apply windowing if specified
        if window and NUMPY_AVAILABLE:
            center, width = window
            vmin = center - width / 2
            vmax = center + width / 2
            ax.imshow(image_data, cmap=self.config.cmap, vmin=vmin, vmax=vmax)
        else:
            ax.imshow(image_data, cmap=self.config.cmap)

        if self.config.show_title and title:
            ax.set_title(title, fontsize=self.config.title_fontsize)

        ax.axis('off')

        if self.config.show_colorbar:
            plt.colorbar(ax.images[0], ax=ax)

        plt.tight_layout()
        return fig

    def show_with_annotations(
        self,
        image_data: Any,
        boxes: List[BoundingBox],
        title: Optional[str] = None
    ) -> Optional[Any]:
        """
        Show image with bounding box annotations.

        Args:
            image_data: Image data
            boxes: List of bounding boxes
            title: Optional title

        Returns:
            matplotlib figure or None
        """
        fig = self.show_image(image_data, title)
        if fig is None:
            return None

        ax = fig.axes[0]

        for box in boxes:
            rect = patches.Rectangle(
                (box.x, box.y),
                box.width,
                box.height,
                linewidth=self.config.annotation_linewidth,
                edgecolor=box.color,
                facecolor='none'
            )
            ax.add_patch(rect)

            # Add label
            ax.text(
                box.x, box.y - 5,
                f"{box.label} ({box.confidence:.0%})",
                color=box.color,
                fontsize=10,
                weight='bold'
            )

        return fig

    def show_comparison(
        self,
        images: List[Any],
        titles: Optional[List[str]] = None,
        main_title: Optional[str] = None
    ) -> Optional[Any]:
        """
        Show multiple images side by side for comparison.

        Args:
            images: List of image data
            titles: Optional list of titles for each image
            main_title: Optional main title

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        n = len(images)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))

        if n == 1:
            axes = [axes]

        for i, (ax, img) in enumerate(zip(axes, images)):
            ax.imshow(img, cmap=self.config.cmap)
            if titles and i < len(titles):
                ax.set_title(titles[i])
            ax.axis('off')

        if main_title:
            fig.suptitle(main_title, fontsize=self.config.title_fontsize)

        plt.tight_layout()
        return fig

    def show_volume_slices(
        self,
        volume: Any,
        num_slices: int = 9,
        title: Optional[str] = None
    ) -> Optional[Any]:
        """
        Show representative slices from a 3D volume.

        Args:
            volume: 3D volume data (H, W, D)
            num_slices: Number of slices to show
            title: Optional title

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            return None

        # Calculate grid size
        cols = int(np.ceil(np.sqrt(num_slices)))
        rows = int(np.ceil(num_slices / cols))

        fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 3 * rows))
        axes = axes.flatten()

        # Select evenly spaced slices
        depth = volume.shape[2]
        slice_indices = np.linspace(0, depth - 1, num_slices, dtype=int)

        for i, (ax, idx) in enumerate(zip(axes, slice_indices)):
            ax.imshow(volume[:, :, idx], cmap=self.config.cmap)
            ax.set_title(f"Slice {idx}")
            ax.axis('off')

        # Hide empty subplots
        for ax in axes[num_slices:]:
            ax.axis('off')

        if title:
            fig.suptitle(title, fontsize=self.config.title_fontsize)

        plt.tight_layout()
        return fig

    def save_figure(
        self,
        fig: Any,
        filepath: Union[str, Path],
        dpi: Optional[int] = None
    ) -> bool:
        """
        Save figure to file.

        Args:
            fig: matplotlib figure
            filepath: Output path
            dpi: Optional DPI override

        Returns:
            True if successful
        """
        try:
            fig.savefig(
                filepath,
                dpi=dpi or self.config.dpi,
                bbox_inches='tight',
                facecolor='white'
            )
            logger.info(f"Saved figure to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save figure: {e}")
            return False


# =============================================================================
# Results Visualization
# =============================================================================

class ResultsVisualizer:
    """
    Visualize analysis results and metrics.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualizer."""
        self.config = config or VisualizationConfig()

    def plot_confidence_scores(
        self,
        findings: List[str],
        confidences: List[float],
        title: str = "Finding Confidence Scores"
    ) -> Optional[Any]:
        """
        Plot confidence scores for findings.

        Args:
            findings: List of finding labels
            confidences: List of confidence scores
            title: Plot title

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(10, max(4, len(findings) * 0.5)))

        # Color based on confidence
        colors = []
        for conf in confidences:
            if conf >= 0.8:
                colors.append('#48bb78')  # Green
            elif conf >= 0.6:
                colors.append('#ecc94b')  # Yellow
            else:
                colors.append('#f56565')  # Red

        y_pos = range(len(findings))
        ax.barh(y_pos, confidences, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(findings)
        ax.set_xlabel('Confidence')
        ax.set_title(title)
        ax.set_xlim(0, 1)

        # Add value labels
        for i, (conf, color) in enumerate(zip(confidences, colors)):
            ax.text(conf + 0.02, i, f'{conf:.0%}', va='center')

        plt.tight_layout()
        return fig

    def plot_processing_times(
        self,
        labels: List[str],
        times_ms: List[float],
        title: str = "Processing Times"
    ) -> Optional[Any]:
        """
        Plot processing times.

        Args:
            labels: Step labels
            times_ms: Times in milliseconds
            title: Plot title

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.bar(labels, times_ms, color='#4299e1')
        ax.set_ylabel('Time (ms)')
        ax.set_title(title)

        # Add value labels
        for i, time in enumerate(times_ms):
            ax.text(i, time + max(times_ms) * 0.02, f'{time:.0f}ms', ha='center')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig

    def plot_longitudinal_trend(
        self,
        dates: List[str],
        values: List[float],
        label: str = "Measurement",
        title: str = "Longitudinal Trend"
    ) -> Optional[Any]:
        """
        Plot longitudinal measurement trend.

        Args:
            dates: List of date strings
            values: Measurement values
            label: Measurement label
            title: Plot title

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(dates, values, 'o-', linewidth=2, markersize=8, label=label)
        ax.set_xlabel('Date')
        ax.set_ylabel(label)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig

    def create_summary_dashboard(
        self,
        findings_data: Dict[str, Any],
        output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Any]:
        """
        Create a summary dashboard of analysis results.

        Args:
            findings_data: Dictionary containing analysis results
            output_path: Optional path to save dashboard

        Returns:
            matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig = plt.figure(figsize=(15, 10))

        # Create grid
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Plot 1: Confidence distribution
        ax1 = fig.add_subplot(gs[0, 0])
        if 'confidences' in findings_data:
            ax1.hist(findings_data['confidences'], bins=10, color='#4299e1', edgecolor='white')
            ax1.set_xlabel('Confidence')
            ax1.set_ylabel('Count')
            ax1.set_title('Confidence Distribution')

        # Plot 2: Finding categories
        ax2 = fig.add_subplot(gs[0, 1])
        if 'categories' in findings_data:
            categories = findings_data['categories']
            ax2.pie(
                list(categories.values()),
                labels=list(categories.keys()),
                autopct='%1.1f%%',
                colors=['#48bb78', '#ecc94b', '#f56565', '#4299e1']
            )
            ax2.set_title('Finding Categories')

        # Plot 3: Processing metrics
        ax3 = fig.add_subplot(gs[1, 0])
        if 'processing_times' in findings_data:
            times = findings_data['processing_times']
            ax3.bar(list(times.keys()), list(times.values()), color='#805ad5')
            ax3.set_ylabel('Time (ms)')
            ax3.set_title('Processing Times')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Plot 4: Summary text
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')

        summary_text = "ANALYSIS SUMMARY\n\n"
        if 'total_findings' in findings_data:
            summary_text += f"Total Findings: {findings_data['total_findings']}\n"
        if 'overall_confidence' in findings_data:
            summary_text += f"Overall Confidence: {findings_data['overall_confidence']:.1%}\n"
        if 'processing_time_total' in findings_data:
            summary_text += f"Total Processing Time: {findings_data['processing_time_total']:.0f}ms\n"

        ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                 family='monospace', transform=ax4.transAxes)
        ax4.set_title('Summary')

        plt.suptitle('RadAssist Pro Analysis Dashboard', fontsize=16, fontweight='bold')

        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            logger.info(f"Dashboard saved to {output_path}")

        return fig


# =============================================================================
# Utility Functions
# =============================================================================

def quick_show(image_data: Any, title: str = "Medical Image") -> None:
    """
    Quick display of an image.

    Args:
        image_data: Image data
        title: Image title
    """
    viz = MedicalImageVisualizer()
    fig = viz.show_image(image_data, title)
    if fig and MATPLOTLIB_AVAILABLE:
        plt.show()


def save_comparison(
    images: List[Any],
    titles: List[str],
    output_path: Union[str, Path],
    main_title: str = "Comparison"
) -> bool:
    """
    Save comparison figure to file.

    Args:
        images: List of images
        titles: List of titles
        output_path: Output file path
        main_title: Main title

    Returns:
        True if successful
    """
    viz = MedicalImageVisualizer()
    fig = viz.show_comparison(images, titles, main_title)

    if fig:
        return viz.save_figure(fig, output_path)
    return False
