"""
Visualization components for longitudinal analysis.

Creates compelling visualizations for the demo video and clinical use.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass
import io
import base64

# Try to import core analyzer
try:
    from src.core.longitudinal_analyzer import (
        NoduleMeasurement,
        ChangeAnalysis,
        LongitudinalReport,
        RiskLevel,
        ChangeTrajectory,
        LungRADSCategory
    )
except ImportError:
    # Define minimal versions for standalone use
    pass


@dataclass
class VisualizationConfig:
    """Configuration for visualizations."""
    figure_width: int = 12
    figure_height: int = 8
    dpi: int = 150
    style: str = "seaborn-v0_8-whitegrid"
    color_improving: str = "#38a169"  # Green
    color_stable: str = "#4299e1"  # Blue
    color_worsening: str = "#e53e3e"  # Red
    color_high_risk: str = "#c53030"  # Dark red
    font_size_title: int = 14
    font_size_label: int = 11


def create_timeline_chart(
    measurements: List[NoduleMeasurement],
    analysis: Optional[ChangeAnalysis] = None,
    config: Optional[VisualizationConfig] = None
) -> plt.Figure:
    """
    Create a timeline chart showing nodule size over time.

    Args:
        measurements: List of nodule measurements
        analysis: Optional analysis results for annotations
        config: Visualization configuration

    Returns:
        Matplotlib figure
    """
    config = config or VisualizationConfig()

    # Extract data
    dates = [m.date for m in measurements]
    sizes = [m.size_mm for m in measurements]

    # Create figure
    fig, ax = plt.subplots(figsize=(config.figure_width, config.figure_height // 2))

    # Determine color based on trajectory
    if analysis:
        if analysis.trajectory == ChangeTrajectory.IMPROVING:
            line_color = config.color_improving
        elif analysis.trajectory == ChangeTrajectory.STABLE:
            line_color = config.color_stable
        else:
            line_color = config.color_worsening
    else:
        line_color = config.color_stable

    # Plot line with markers
    ax.plot(dates, sizes, '-o', color=line_color, linewidth=2, markersize=10,
            markerfacecolor='white', markeredgewidth=2)

    # Add size labels
    for date, size in zip(dates, sizes):
        ax.annotate(f'{size}mm', (date, size), textcoords="offset points",
                    xytext=(0, 10), ha='center', fontsize=config.font_size_label,
                    fontweight='bold')

    # Add threshold lines for Lung-RADS
    ax.axhline(y=6, color='gray', linestyle='--', alpha=0.5, label='Lung-RADS 2/3 threshold')
    ax.axhline(y=8, color='orange', linestyle='--', alpha=0.5, label='Lung-RADS 3/4A threshold')
    ax.axhline(y=15, color='red', linestyle='--', alpha=0.5, label='Lung-RADS 4A/4B threshold')

    # Styling
    ax.set_xlabel('Date', fontsize=config.font_size_label)
    ax.set_ylabel('Nodule Size (mm)', fontsize=config.font_size_label)
    ax.set_title('Nodule Size Over Time', fontsize=config.font_size_title, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)

    # Set y-axis to start from 0
    ax.set_ylim(bottom=0, top=max(sizes) * 1.3)

    # Format dates
    fig.autofmt_xdate()

    plt.tight_layout()
    return fig


def create_growth_rate_chart(
    measurements: List[NoduleMeasurement],
    config: Optional[VisualizationConfig] = None
) -> plt.Figure:
    """
    Create a bar chart showing growth rates between timepoints.

    Args:
        measurements: List of nodule measurements
        config: Visualization configuration

    Returns:
        Matplotlib figure
    """
    config = config or VisualizationConfig()

    if len(measurements) < 2:
        raise ValueError("Need at least 2 measurements for growth rate chart")

    # Calculate growth rates
    intervals = []
    growth_rates = []

    for i in range(1, len(measurements)):
        prior = measurements[i - 1]
        current = measurements[i]

        days_between = (current.date - prior.date).days
        size_change = current.size_mm - prior.size_mm
        pct_change = (size_change / prior.size_mm) * 100

        interval_label = f"{prior.date.strftime('%Y-%m')}\nto\n{current.date.strftime('%Y-%m')}"
        intervals.append(interval_label)
        growth_rates.append(pct_change)

    # Create figure
    fig, ax = plt.subplots(figsize=(config.figure_width, config.figure_height // 2))

    # Color bars based on growth rate
    colors = []
    for rate in growth_rates:
        if rate < -5:
            colors.append(config.color_improving)
        elif rate < 5:
            colors.append(config.color_stable)
        else:
            colors.append(config.color_worsening)

    bars = ax.bar(intervals, growth_rates, color=colors, edgecolor='black', linewidth=1)

    # Add value labels
    for bar, rate in zip(bars, growth_rates):
        height = bar.get_height()
        ax.annotate(f'{rate:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=config.font_size_label,
                    fontweight='bold')

    # Reference line at 0
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    # Styling
    ax.set_xlabel('Interval', fontsize=config.font_size_label)
    ax.set_ylabel('Growth Rate (%)', fontsize=config.font_size_label)
    ax.set_title('Interval Growth Rates', fontsize=config.font_size_title, fontweight='bold')

    plt.tight_layout()
    return fig


def create_vdt_gauge(
    vdt_days: float,
    config: Optional[VisualizationConfig] = None
) -> plt.Figure:
    """
    Create a gauge chart showing volume doubling time risk.

    Args:
        vdt_days: Volume doubling time in days
        config: Visualization configuration

    Returns:
        Matplotlib figure
    """
    config = config or VisualizationConfig()

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw={'projection': 'polar'})

    # VDT thresholds (days)
    # < 200: Very high risk
    # 200-400: High risk
    # 400-600: Moderate risk
    # > 600: Low risk

    # Normalize VDT to 0-1 scale (inverted - lower VDT = higher risk)
    max_vdt = 800
    normalized = min(1, vdt_days / max_vdt)

    # Calculate angle (0 = high risk, π = low risk)
    theta = normalized * np.pi

    # Draw gauge background
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    # Create colored arc segments
    colors_arc = ['#c53030', '#e53e3e', '#d69e2e', '#38a169']
    thresholds = [0, 0.25, 0.5, 0.75, 1.0]  # 200, 400, 600 days

    for i in range(len(colors_arc)):
        start_angle = thresholds[i] * np.pi
        end_angle = thresholds[i + 1] * np.pi
        angles = np.linspace(start_angle, end_angle, 30)
        radii = np.ones(30) * 0.9
        ax.fill_between(angles, 0.7, radii, color=colors_arc[i], alpha=0.6)

    # Draw needle
    ax.plot([theta, theta], [0, 0.8], color='black', linewidth=3)
    ax.scatter([theta], [0.8], s=100, color='black', zorder=5)

    # Remove radial ticks
    ax.set_rticks([])
    ax.set_xticks([])

    # Add labels
    ax.text(0, -0.1, 'HIGH\nRISK', ha='center', va='center', fontsize=10, color='#c53030')
    ax.text(np.pi, -0.1, 'LOW\nRISK', ha='center', va='center', fontsize=10, color='#38a169')

    # Title with VDT value
    plt.title(f'Volume Doubling Time: {vdt_days:.0f} days', fontsize=config.font_size_title,
              fontweight='bold', y=1.1)

    plt.tight_layout()
    return fig


def create_risk_summary_card(
    analysis: ChangeAnalysis,
    config: Optional[VisualizationConfig] = None
) -> plt.Figure:
    """
    Create a summary card showing key risk metrics.

    Args:
        analysis: Analysis results
        config: Visualization configuration

    Returns:
        Matplotlib figure
    """
    config = config or VisualizationConfig()

    fig = plt.figure(figsize=(10, 6))
    gs = GridSpec(2, 3, figure=fig)

    # Risk level color
    risk_colors = {
        RiskLevel.LOW: '#38a169',
        RiskLevel.INTERMEDIATE: '#d69e2e',
        RiskLevel.HIGH: '#e53e3e',
        RiskLevel.VERY_HIGH: '#c53030'
    }

    risk_color = risk_colors.get(analysis.risk_level, '#718096')

    # Main risk indicator (spans 2 rows)
    ax_risk = fig.add_subplot(gs[:, 0])
    ax_risk.set_facecolor(risk_color)
    ax_risk.text(0.5, 0.6, 'RISK', ha='center', va='center', fontsize=16,
                 color='white', fontweight='bold')
    ax_risk.text(0.5, 0.4, analysis.risk_level.value.upper().replace('_', '\n'),
                 ha='center', va='center', fontsize=20, color='white', fontweight='bold')
    ax_risk.set_xticks([])
    ax_risk.set_yticks([])

    # Size change
    ax_size = fig.add_subplot(gs[0, 1])
    ax_size.text(0.5, 0.6, 'Size Change', ha='center', va='center', fontsize=12)
    ax_size.text(0.5, 0.35, f'+{analysis.size_change_mm:.1f}mm', ha='center', va='center',
                 fontsize=18, fontweight='bold', color=risk_color)
    ax_size.text(0.5, 0.15, f'({analysis.size_change_percent:.1f}%)', ha='center', va='center',
                 fontsize=11, color='#718096')
    ax_size.set_xticks([])
    ax_size.set_yticks([])
    ax_size.set_facecolor('#f7fafc')

    # Volume change
    ax_vol = fig.add_subplot(gs[0, 2])
    ax_vol.text(0.5, 0.6, 'Volume Change', ha='center', va='center', fontsize=12)
    ax_vol.text(0.5, 0.35, f'+{analysis.volume_change_percent:.1f}%', ha='center', va='center',
                fontsize=18, fontweight='bold', color=risk_color)
    ax_vol.set_xticks([])
    ax_vol.set_yticks([])
    ax_vol.set_facecolor('#f7fafc')

    # VDT
    ax_vdt = fig.add_subplot(gs[1, 1])
    ax_vdt.text(0.5, 0.6, 'Vol. Doubling Time', ha='center', va='center', fontsize=12)
    if analysis.volume_doubling_time_days:
        vdt_text = f'{analysis.volume_doubling_time_days:.0f} days'
    else:
        vdt_text = 'N/A'
    ax_vdt.text(0.5, 0.35, vdt_text, ha='center', va='center',
                fontsize=18, fontweight='bold', color=risk_color)
    ax_vdt.set_xticks([])
    ax_vdt.set_yticks([])
    ax_vdt.set_facecolor('#f7fafc')

    # Lung-RADS
    ax_rads = fig.add_subplot(gs[1, 2])
    ax_rads.text(0.5, 0.6, 'Lung-RADS', ha='center', va='center', fontsize=12)
    if analysis.lung_rads_current:
        rads_text = f'Category {analysis.lung_rads_current.value}'
    else:
        rads_text = 'N/A'
    ax_rads.text(0.5, 0.35, rads_text, ha='center', va='center',
                 fontsize=16, fontweight='bold', color=risk_color)
    ax_rads.set_xticks([])
    ax_rads.set_yticks([])
    ax_rads.set_facecolor('#f7fafc')

    plt.tight_layout()
    return fig


def fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64 string for embedding in HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


def create_all_visualizations(
    measurements: List[NoduleMeasurement],
    analysis: ChangeAnalysis
) -> dict:
    """
    Create all visualizations for longitudinal analysis.

    Args:
        measurements: List of nodule measurements
        analysis: Analysis results

    Returns:
        Dictionary of visualization names to base64 image strings
    """
    visualizations = {}

    try:
        # Timeline chart
        fig = create_timeline_chart(measurements, analysis)
        visualizations['timeline'] = fig_to_base64(fig)
    except Exception as e:
        print(f"Error creating timeline chart: {e}")

    try:
        # Growth rate chart
        fig = create_growth_rate_chart(measurements)
        visualizations['growth_rates'] = fig_to_base64(fig)
    except Exception as e:
        print(f"Error creating growth rate chart: {e}")

    try:
        # VDT gauge
        if analysis.volume_doubling_time_days:
            fig = create_vdt_gauge(analysis.volume_doubling_time_days)
            visualizations['vdt_gauge'] = fig_to_base64(fig)
    except Exception as e:
        print(f"Error creating VDT gauge: {e}")

    try:
        # Risk summary card
        fig = create_risk_summary_card(analysis)
        visualizations['risk_summary'] = fig_to_base64(fig)
    except Exception as e:
        print(f"Error creating risk summary: {e}")

    return visualizations


if __name__ == "__main__":
    # Demo visualization
    from src.core.longitudinal_analyzer import (
        NoduleMeasurement,
        analyze_longitudinal_change,
        create_longitudinal_report
    )

    measurements = [
        NoduleMeasurement(datetime(2024, 1, 15), 6.0, "RUL"),
        NoduleMeasurement(datetime(2024, 7, 20), 6.2, "RUL"),
        NoduleMeasurement(datetime(2025, 1, 18), 6.8, "RUL"),
        NoduleMeasurement(datetime(2025, 7, 15), 8.3, "RUL"),
    ]

    report = create_longitudinal_report(measurements, "Demo patient")

    print("Creating visualizations...")
    viz = create_all_visualizations(measurements, report.analysis)
    print(f"Created {len(viz)} visualizations: {list(viz.keys())}")

    # Save one as example
    import re

    # Extract and save timeline image
    if 'timeline' in viz:
        img_data = viz['timeline'].split(',')[1]
        with open('/tmp/timeline_demo.png', 'wb') as f:
            f.write(base64.b64decode(img_data))
        print("Saved timeline demo to /tmp/timeline_demo.png")
