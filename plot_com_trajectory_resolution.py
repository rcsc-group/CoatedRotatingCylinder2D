#!/usr/bin/env python3

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# -----------------------------------------------------------------------------
# Grid-resolution comparison for spatial coating trajectories
#
# Overlays several maximum AMR levels using:
#
#   - coating centre-of-mass trajectories;
#   - tracked maximum-thickness trajectories;
#   - final saved liquid interfaces;
#   - one neutral unit-radius cylinder.
#
# Resolution is encoded by colour. Line style and marker shape distinguish
# the physical diagnostics.
#
# Usage:
#   python3 plot_com_trajectory_resolution.py
#   python3 plot_com_trajectory_resolution.py --levels 7 8 9 10 11
#   python3 plot_com_trajectory_resolution.py --save-only --no-tex
#   python3 plot_com_trajectory_resolution.py --output-root output
#
# Requires:
#   postprocess_common.py in the same directory
#   NumPy
#   Matplotlib
#   Pylustrator, unless --save-only is used
# -----------------------------------------------------------------------------

"""Grid-resolution comparison for spatial coating trajectories."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
import numpy as np

from postprocess_common import (
    Case,
    KeyEntry,
    TrackingOptions,
    add_key_panel,
    apply_publication_style,
    base_parser,
    load_spatial,
    relative_bounds,
    resolution_colours,
    resolve_output_root,
    save_figure,
    start_plotting,
)


# -----------------------------------------------------------------------------
# User-configurable case, tracking and output settings
# -----------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

CASE = Case(
    film_radius_tag="1.5",
    cylinder_velocity_tag="1.0",
)

DEFAULT_LEVELS = [7, 8, 9, 10, 11]
COMPONENT_ID = 0
TRACKING = TrackingOptions()

OUTPUT_NAME = "centre_of_mass_resolution_comparison"


# -----------------------------------------------------------------------------
# Command-line configuration
# -----------------------------------------------------------------------------

parser = base_parser(__doc__)
parser.add_argument(
    "--levels",
    nargs="+",
    type=int,
    default=DEFAULT_LEVELS,
    help="maximum AMR levels to compare",
)
args = parser.parse_args()

OUTPUT_ROOT = resolve_output_root(PROJECT_DIR, args.output_root)

levels = args.levels
colours = resolution_colours(levels)


# -----------------------------------------------------------------------------
# Plotting setup
# -----------------------------------------------------------------------------

start_plotting(edit=not args.save_only)
apply_publication_style(
    use_tex=not args.no_tex,
    dpi=args.dpi,
)

fig, ax = plt.subplots(
    num=1,
    clear=True,
    figsize=(5.6, 5.6),
)
ax.set_label("main_axes")


# -----------------------------------------------------------------------------
# Reconstruct and plot each available resolution level
# -----------------------------------------------------------------------------

loaded = []
all_x = []
all_y = []

for level, colour in zip(levels, colours):
    try:
        result = load_spatial(
            OUTPUT_ROOT,
            CASE,
            level,
            component_id=COMPONENT_ID,
            tracking=TRACKING,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Skipping L={level}: {error}")
        continue

    loaded.append((level, colour, result))

    # Use transparent fills so overlapping converged shapes remain visible.
    ax.fill(
        result.final_polygon[:, 0],
        result.final_polygon[:, 1],
        facecolor=colour,
        edgecolor="none",
        alpha=0.08,
        zorder=1,
    )

    # Use line style and markers to distinguish the physical diagnostics.
    ax.plot(
        result.final_polygon[:, 0],
        result.final_polygon[:, 1],
        color=colour,
        linewidth=1.0,
        zorder=4,
    )
    ax.plot(
        result.com_x,
        result.com_y,
        color=colour,
        linewidth=2.0,
        zorder=7,
    )
    ax.plot(
        result.maximum_x,
        result.maximum_y,
        color=colour,
        linestyle="--",
        linewidth=1.7,
        zorder=6,
    )

    # Mark the final CoM and maximum-thickness locations.
    ax.plot(
        result.com_x[-1],
        result.com_y[-1],
        marker="o",
        color=colour,
        markersize=4.5,
        linestyle="none",
        zorder=8,
    )
    ax.plot(
        result.maximum_x[-1],
        result.maximum_y[-1],
        marker="s",
        color=colour,
        markersize=4.0,
        linestyle="none",
        zorder=8,
    )

    # Collect all coordinates for a common equal-aspect plotting extent.
    all_x.extend((
        result.final_points[:, 0],
        result.com_x,
        result.maximum_x,
    ))
    all_y.extend((
        result.final_points[:, 1],
        result.com_y,
        result.maximum_y,
    ))

    print(
        f"L={level}: "
        f"t_end={result.final_time:g}, "
        f"CoM=({result.com_x[-1]:.10g}, "
        f"{result.com_y[-1]:.10g}), "
        f"file={result.final_file}"
    )

if not loaded:
    raise FileNotFoundError(
        "No complete resolution cases were found."
    )


# -----------------------------------------------------------------------------
# Cylinder geometry and common spatial formatting
# -----------------------------------------------------------------------------

ax.add_patch(
    Circle(
        (0.0, 0.0),
        radius=1.0,
        facecolor="0.84",
        edgecolor="0.05",
        linewidth=1.5,
        alpha=0.75,
        zorder=2,
    )
)

ax.plot(
    [0.0, 1.0],
    [0.0, 0.0],
    color="0.20",
    linewidth=0.9,
    zorder=3,
)
ax.plot(
    0.0,
    0.0,
    "o",
    color="0.10",
    markersize=2.5,
    zorder=9,
)
ax.text(
    0.52,
    0.06,
    r"$R=1$",
    ha="center",
    va="bottom",
    zorder=9,
)

all_x = np.concatenate(all_x)
all_y = np.concatenate(all_y)

extent = max(
    np.max(np.abs(all_x)),
    np.max(np.abs(all_y)),
    1.0,
)
margin = 0.10*extent

ax.set_xlim(-extent - margin, extent + margin)
ax.set_ylim(-extent - margin, extent + margin)
ax.set_aspect("equal", adjustable="box")

ax.set_xlabel(r"$x$")
ax.set_ylabel(r"$y$")
ax.set_title(
    rf"$c_R={CASE.film_radius:g},\quad "
    rf"c_V={CASE.cylinder_velocity:g}$"
)

ax.set_axisbelow(True)
ax.minorticks_on()
ax.grid(
    True,
    which="major",
    color="0.86",
    linewidth=0.7,
)
ax.grid(
    True,
    which="minor",
    color="0.93",
    linewidth=0.45,
    linestyle=":",
)


# -----------------------------------------------------------------------------
# Diagnostic legend and stable resolution key
# -----------------------------------------------------------------------------

diagnostic_legend = ax.legend(
    handles=[
        Line2D(
            [0],
            [0],
            color="0.15",
            linewidth=2.0,
            marker="o",
            markersize=4.5,
            label="Centre of mass",
        ),
        Line2D(
            [0],
            [0],
            color="0.15",
            linestyle="--",
            linewidth=1.7,
            marker="s",
            markersize=4.0,
            label="Maximum film thickness",
        ),
        Line2D(
            [0],
            [0],
            color="0.15",
            linewidth=1.0,
            label="Final interface",
        ),
    ],
    frameon=True,
    framealpha=1.0,
    facecolor="white",
    edgecolor="0.25",
    loc="upper left",
)

# Complete the main-axes layout before positioning the independent key panel.
fig.tight_layout()

resolution_entries = [
    KeyEntry(
        label=rf"Level$={level}$",
        colour=colour,
        linewidth=2.0,
    )
    for level, colour, _ in loaded
]

resolution_key_panel = add_key_panel(
    fig,
    relative_bounds(
        ax,
        [0.52, 0.65, 0.44, 0.29],
    ),
    resolution_entries,
    label="resolution_key_panel",
    title="Maximum AMR level",
    ncol=2,
)


# -----------------------------------------------------------------------------
# Interactive editing and export
# -----------------------------------------------------------------------------

# Pylustrator writes its generated Matplotlib commands immediately above
# this call when Ctrl+S is pressed. Keep this location unobstructed.
if not args.save_only:
    plt.show()

output = PROJECT_DIR / OUTPUT_NAME
save_figure(
    fig,
    output,
    dpi=args.dpi,
)
