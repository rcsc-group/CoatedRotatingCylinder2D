#!/usr/bin/env python3

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# -----------------------------------------------------------------------------
# Shared Basilisk post-processing utilities
#
# Provides the reusable infrastructure used by the four coated-cylinder
# post-processing scripts:
#
#   - case-directory construction;
#   - diagnostic-file loading and validation;
#   - Basilisk interface reconstruction;
#   - continuous maximum-thickness tracking;
#   - publication-oriented Matplotlib styling;
#   - stable custom key panels;
#   - vector and high-resolution raster export.
#
# This file is a local helper module and is not intended to be run directly.
# Keep it in the same directory as the four executable plotting scripts.
#
# Requires:
#   NumPy
#   Matplotlib
#   Pylustrator, when interactive editing is requested
# -----------------------------------------------------------------------------

"""Shared, problem-independent helpers for Basilisk post-processing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
from typing import Sequence

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np


# -----------------------------------------------------------------------------
# Lightweight data containers
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Case:
    """Case tags used numerically and in the Basilisk output-directory name."""

    film_radius_tag: str = "1.5"
    cylinder_velocity_tag: str = "1.0"

    @property
    def film_radius(self) -> float:
        """Return the coating radius as a floating-point value."""
        return float(self.film_radius_tag)

    @property
    def cylinder_velocity(self) -> float:
        """Return the cylinder velocity as a floating-point value."""
        return float(self.cylinder_velocity_tag)

    def directory(self, output_root: Path, level: int) -> Path:
        """Resolve the output directory for one parameter combination.

        The current sweep driver writes directories as
        ``fR_<radius>_cV_<velocity>_L_<level>``. An exact textual match is
        preferred, while a numeric fallback accepts equivalent tags such as
        ``1``, ``1.0`` and ``1.00``.
        """
        output_root = Path(output_root)
        expected = (
            output_root
            / (
                f"fR_{self.film_radius_tag}_"
                f"cV_{self.cylinder_velocity_tag}_L_{level}"
            )
        )

        if expected.is_dir():
            return expected

        if not output_root.is_dir():
            raise FileNotFoundError(f"Missing output root: {output_root}")

        number = (
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
            r"(?:[eE][+-]?\d+)?"
        )
        pattern = re.compile(
            rf"^fR_(?P<radius>{number})_"
            rf"cV_(?P<velocity>{number})_"
            rf"L_(?P<level>\d+)$"
        )

        matches = []

        for candidate in output_root.iterdir():
            if not candidate.is_dir():
                continue

            match = pattern.fullmatch(candidate.name)

            if match is None:
                continue

            same_radius = np.isclose(
                float(match.group("radius")),
                self.film_radius,
                rtol=0.0,
                atol=1.0e-12,
            )
            same_velocity = np.isclose(
                float(match.group("velocity")),
                self.cylinder_velocity,
                rtol=0.0,
                atol=1.0e-12,
            )
            same_level = int(match.group("level")) == int(level)

            if same_radius and same_velocity and same_level:
                matches.append(candidate)

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            names = ", ".join(sorted(path.name for path in matches))
            raise ValueError(
                "Ambiguous numerically equivalent case directories: "
                f"{names}"
            )

        raise FileNotFoundError(
            "No case directory matching "
            f"fRadius={self.film_radius_tag}, "
            f"cV={self.cylinder_velocity_tag}, "
            f"MAX_LEVEL={level} under {output_root}"
        )


@dataclass(frozen=True)
class TrackingOptions:
    """Controls for tracking a continuous maximum-thickness branch."""

    angular_bins: int = 720
    smoothing_window: int = 11
    maximum_band: float = 3.0e-3
    initial_angle: float = -0.5*np.pi


@dataclass(frozen=True)
class ThicknessData:
    """Time history of the minimum and maximum film thickness."""

    time: np.ndarray
    minimum: np.ndarray
    maximum: np.ndarray


@dataclass(frozen=True)
class SpatialData:
    """Spatial diagnostics reconstructed for one maximum AMR level."""

    level: int
    final_time: float
    final_file: Path
    com_x: np.ndarray
    com_y: np.ndarray
    maximum_x: np.ndarray
    maximum_y: np.ndarray
    final_points: np.ndarray
    final_polygon: np.ndarray


@dataclass(frozen=True)
class KeyEntry:
    """One line-and-text entry in a stable custom key panel."""

    label: str
    colour: object
    linestyle: str = "-"
    linewidth: float = 1.5
    value: str | None = None


# -----------------------------------------------------------------------------
# Common command-line and plotting setup
# -----------------------------------------------------------------------------


def base_parser(description: str) -> argparse.ArgumentParser:
    """Return the command-line options shared by all plotting scripts."""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--output-root",
        default="output",
        help=(
            "simulation-output root; relative paths are resolved beside the "
            "plotting scripts; default: output"
        ),
    )

    parser.add_argument(
        "--save-only",
        action="store_true",
        help="save the figure without opening Pylustrator",
    )
    parser.add_argument(
        "--no-tex",
        action="store_true",
        help="disable external LaTeX text rendering",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="PNG resolution; default: 600",
    )

    return parser


def resolve_output_root(project_dir: Path, value: str | Path) -> Path:
    """Resolve an output-root argument relative to the plotting-suite folder."""
    path = Path(value).expanduser()

    if not path.is_absolute():
        path = project_dir/path

    return path.resolve()


def start_plotting(edit: bool) -> None:
    """Start from a clean figure registry and optionally enable Pylustrator."""
    # This makes repeated execution safe in persistent Spyder/IPython sessions.
    plt.close("all")

    if edit:
        # Pylustrator must be started before any Matplotlib figures are created.
        import pylustrator

        pylustrator.start(use_global_variable_names=True)


def apply_publication_style(*, use_tex: bool, dpi: int) -> None:
    """Apply one restrained publication style across all four figures."""
    plt.rcParams.update({
        "text.usetex": use_tex,
        "font.family": "serif",
        "mathtext.fontset": "stix",
        "font.size": 10,
        "axes.labelsize": 12,
        "axes.titlesize": 11,
        "legend.fontsize": 9,
        "legend.title_fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.linewidth": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "savefig.dpi": dpi,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    })


def save_figure(fig, output: Path, *, dpi: int) -> None:
    """Save PDF and PNG outputs, then release the Matplotlib figure."""
    pdf = output.with_suffix(".pdf")
    png = output.with_suffix(".png")

    # PDF preserves vector lines and text; PNG is retained for previews and
    # platforms that do not render PDF figures directly.
    fig.savefig(pdf)
    fig.savefig(png, dpi=dpi)

    # Explicitly deregister the figure for safe repeated execution.
    plt.close(fig)

    print(f"Saved {pdf}")
    print(f"Saved {png} at {dpi} dpi")


def resolution_colours(levels: Sequence[int]) -> list[object]:
    """Return exactly one muted red-to-blue colour per requested AMR level."""
    if not levels:
        raise ValueError("At least one resolution level is required.")

    # Sampling from a continuous colormap prevents zip() from silently
    # truncating the level list when additional resolutions are introduced.
    cmap = LinearSegmentedColormap.from_list(
        "resolution_levels",
        ["#8B1E3F", "#B85C5C", "#8A8290", "#4F79A7", "#173F5F"],
    )

    return list(cmap(np.linspace(0.0, 1.0, len(levels))))


# -----------------------------------------------------------------------------
# Thickness diagnostics
# -----------------------------------------------------------------------------


def load_thickness(
    output_root: Path,
    case: Case,
    level: int,
) -> ThicknessData:
    """Load time and minimum/maximum film thickness from logvol.dat."""
    logfile = case.directory(output_root, level) / "logvol.dat"

    if not logfile.is_file():
        raise FileNotFoundError(f"Missing thickness log: {logfile}")

    # atleast_2d preserves column indexing for a one-row diagnostic file.
    data = np.atleast_2d(np.loadtxt(logfile))

    if data.shape[1] < 8:
        raise ValueError(
            f"Expected at least eight columns in {logfile}; "
            f"found {data.shape[1]}."
        )

    # Columns 6 and 7 contain the minimum and maximum radial coordinates.
    # Subtract the unit cylinder radius to obtain the film thickness h - 1.
    return ThicknessData(
        time=data[:, 1],
        minimum=data[:, 6] - 1.0,
        maximum=data[:, 7] - 1.0,
    )


# -----------------------------------------------------------------------------
# Basilisk interface reconstruction
# -----------------------------------------------------------------------------


def read_interface(path: Path) -> np.ndarray:
    """Read Basilisk output_facets data as independent line segments."""
    segments: list[list[list[float]]] = []
    block: list[list[float]] = []

    def flush() -> None:
        """Convert the current block of vertices into two-point segments."""
        nonlocal block

        if len(block) >= 2:
            segments.extend(
                [block[index:index + 2]]
                for index in range(0, len(block) - 1, 2)
            )

        block = []

    with path.open() as stream:
        for line in stream:
            values = line.split()

            # Blank lines delimit independent facet blocks.
            if len(values) < 2:
                flush()
                continue

            block.append([float(values[0]), float(values[1])])

    flush()

    if not segments:
        raise ValueError(f"No interface segments found in {path}")

    return np.asarray(segments, dtype=float)


def interface_time(path: Path) -> float:
    """Extract nondimensional time from interfacesLiquid-<time>.dat."""
    match = re.search(r"interfacesLiquid-([0-9.eE+-]+)\.dat$", path.name)

    if match is None:
        raise ValueError(f"Cannot read interface time from {path.name}")

    return float(match.group(1))


def interface_points(segments: np.ndarray) -> np.ndarray:
    """Return unique interface vertices for geometric post-processing."""
    points = segments.reshape(-1, 2)

    # Rounding suppresses insignificant floating-point differences between
    # vertices shared by adjacent Basilisk facets.
    return np.unique(np.round(points, decimals=12), axis=0)


# -----------------------------------------------------------------------------
# Maximum-thickness tracking
# -----------------------------------------------------------------------------


def radial_profile(
    points: np.ndarray,
    options: TrackingOptions,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct a lightly smoothed periodic outer-radius profile."""
    theta = np.mod(np.arctan2(points[:, 1], points[:, 0]), 2.0*np.pi)
    radius = np.hypot(points[:, 0], points[:, 1])

    # Bin the interface in polar angle and retain the outermost radius in
    # each bin. This produces a star-shaped radius representation.
    edges = np.linspace(0.0, 2.0*np.pi, options.angular_bins + 1)
    centres = 0.5*(edges[:-1] + edges[1:])
    indices = np.floor(
        theta/(2.0*np.pi)*options.angular_bins
    ).astype(int)
    indices = np.clip(indices, 0, options.angular_bins - 1)

    profile = np.full(options.angular_bins, np.nan)

    for index, value in zip(indices, radius):
        if np.isnan(profile[index]) or value > profile[index]:
            profile[index] = value

    valid = np.isfinite(profile)

    if np.count_nonzero(valid) < 3:
        raise ValueError("Insufficient interface points for a polar profile.")

    # Periodically interpolate angular bins that contain no interface vertex.
    valid_theta = centres[valid]
    valid_radius = profile[valid]

    extended_theta = np.concatenate((
        valid_theta[-1:] - 2.0*np.pi,
        valid_theta,
        valid_theta[:1] + 2.0*np.pi,
    ))
    extended_radius = np.concatenate((
        valid_radius[-1:],
        valid_radius,
        valid_radius[:1],
    ))
    profile = np.interp(centres, extended_theta, extended_radius)

    # Apply a circular moving average to suppress grid-scale extrema.
    window = max(1, int(options.smoothing_window))

    if window % 2 == 0:
        window += 1

    if window > 1:
        half = window//2
        padded = np.concatenate((
            profile[-half:],
            profile,
            profile[:half],
        ))
        profile = np.convolve(
            padded,
            np.ones(window)/window,
            mode="valid",
        )

    return centres, profile


def tracked_maximum(
    points: np.ndarray,
    previous_angle: float,
    options: TrackingOptions,
) -> tuple[np.ndarray, float]:
    """Select a near-global maximum continuous with the previous snapshot."""
    theta, radius = radial_profile(points, options)
    maximum_radius = np.max(radius)

    # Near-degenerate maxima are resolved by angular continuity, preventing
    # the tracked point from jumping between distinct branches.
    candidates = np.flatnonzero(
        radius >= maximum_radius*(1.0 - options.maximum_band)
    )

    angular_distance = np.abs(
        np.angle(np.exp(1j*(theta[candidates] - previous_angle)))
    )
    index = candidates[np.argmin(angular_distance)]

    angle = theta[index]
    point = radius[index]*np.array([np.cos(angle), np.sin(angle)])

    return point, angle


def load_spatial(
    output_root: Path,
    case: Case,
    level: int,
    *,
    component_id: int = 0,
    tracking: TrackingOptions | None = None,
) -> SpatialData:
    """Load CoM, tracked maximum and final interface for one AMR level."""
    options = tracking or TrackingOptions()
    case_dir = case.directory(output_root, level)

    droplet_file = case_dir / "logdroplets.dat"
    interface_dir = case_dir / "Interfaces"

    # Read and validate the connected-component diagnostics.
    if not droplet_file.is_file():
        raise FileNotFoundError(f"Missing centre-of-mass log: {droplet_file}")

    droplets = np.atleast_2d(np.loadtxt(droplet_file))

    if droplets.shape[1] < 6:
        raise ValueError(
            f"Expected at least six columns in {droplet_file}; "
            f"found {droplets.shape[1]}."
        )

    droplets = droplets[droplets[:, 2].astype(int) == component_id]

    if droplets.size == 0:
        raise ValueError(
            f"Component {component_id} is absent from {droplet_file}"
        )

    # Sort interface snapshots by the time encoded in their filenames.
    interface_files = sorted(
        interface_dir.glob("interfacesLiquid-*.dat"),
        key=interface_time,
    )

    if not interface_files:
        raise FileNotFoundError(
            f"No interface files found in {interface_dir}"
        )

    # Prepend the known initial centre-of-mass position.
    com_x = np.concatenate(([0.0], droplets[:, 4]))
    com_y = np.concatenate(([0.0], droplets[:, 5]))

    # Initialise and track one continuous maximum-thickness branch.
    maximum_x = [case.film_radius*np.cos(options.initial_angle)]
    maximum_y = [case.film_radius*np.sin(options.initial_angle)]
    previous_angle = np.mod(options.initial_angle, 2.0*np.pi)

    for interface_file in interface_files:
        points = interface_points(read_interface(interface_file))
        point, previous_angle = tracked_maximum(
            points,
            previous_angle,
            options,
        )

        maximum_x.append(point[0])
        maximum_y.append(point[1])

    # Use the final saved interface as the converged coating shape.
    final_file = interface_files[-1]
    final_points = interface_points(read_interface(final_file))

    # Order the star-shaped interface by polar angle and close the polygon.
    final_theta = np.arctan2(final_points[:, 1], final_points[:, 0])
    final_polygon = final_points[np.argsort(final_theta)]
    final_polygon = np.vstack((final_polygon, final_polygon[0]))

    return SpatialData(
        level=level,
        final_time=interface_time(final_file),
        final_file=final_file,
        com_x=com_x,
        com_y=com_y,
        maximum_x=np.asarray(maximum_x),
        maximum_y=np.asarray(maximum_y),
        final_points=final_points,
        final_polygon=final_polygon,
    )


# -----------------------------------------------------------------------------
# Stable custom key panels
# -----------------------------------------------------------------------------


def relative_bounds(ax, bounds: Sequence[float]) -> list[float]:
    """Convert axes-relative bounds to Matplotlib figure coordinates."""
    x, y, width, height = bounds
    box = ax.get_position()

    return [
        box.x0 + x*box.width,
        box.y0 + y*box.height,
        width*box.width,
        height*box.height,
    ]


def add_key_panel(
    fig,
    bounds: Sequence[float],
    entries: Sequence[KeyEntry],
    *,
    label: str,
    title: str | None = None,
    ncol: int = 1,
    fontsize: float = 9,
):
    """Draw a repeatable legend-like panel using only ordinary artists."""
    if not entries:
        raise ValueError("A key panel requires at least one entry.")

    # A dedicated axes is more stable under repeated Pylustrator execution
    # than a second Matplotlib Legend object attached with ax.add_artist().
    panel = fig.add_axes(bounds, label=label)
    panel.set_xlim(0.0, 1.0)
    panel.set_ylim(0.0, 1.0)
    panel.set_xticks([])
    panel.set_yticks([])
    panel.set_facecolor("white")
    panel.set_zorder(20)

    # Use the axes spines as the visible frame around the key.
    for spine in panel.spines.values():
        spine.set_visible(True)
        spine.set_color("0.25")
        spine.set_linewidth(0.8)

    if title:
        panel.text(
            0.5,
            0.86,
            title,
            ha="center",
            va="center",
            fontsize=fontsize,
        )

    # Divide the available width into equal columns.
    nentry = len(entries)
    ncol = max(1, min(int(ncol), nentry))
    nrow = int(np.ceil(nentry/ncol))

    left_margin = 0.055
    right_margin = 0.035
    column_width = (1.0 - left_margin - right_margin)/ncol
    sample_width = min(0.105, 0.25*column_width)
    text_gap = 0.030

    top = 0.62 if title else 0.74
    bottom = 0.18 if title else 0.26

    row_positions = (
        np.array([(top + bottom)/2.0])
        if nrow == 1
        else np.linspace(top, bottom, nrow)
    )

    # Fill columns from top to bottom for a compact, predictable layout.
    for index, entry in enumerate(entries):
        column = index//nrow
        row = index % nrow

        x_start = left_margin + column*column_width
        x_end = x_start + sample_width
        x_text = x_end + text_gap
        y0 = row_positions[row]

        panel.plot(
            [x_start, x_end],
            [y0, y0],
            color=entry.colour,
            linestyle=entry.linestyle,
            linewidth=entry.linewidth,
            solid_capstyle="butt",
            clip_on=True,
        )
        panel.text(
            x_text,
            y0,
            entry.label,
            ha="left",
            va="center",
            fontsize=fontsize,
            clip_on=True,
        )

        # Optional right-aligned values prevent long entries from being
        # squeezed beyond the key frame.
        if entry.value is not None:
            panel.text(
                0.95,
                y0,
                entry.value,
                ha="right",
                va="center",
                fontsize=fontsize,
                clip_on=True,
            )

    return panel