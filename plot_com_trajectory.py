#!/usr/bin/env python3

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# -----------------------------------------------------------------------------
# Centre-of-mass and maximum-thickness trajectories
#
# Reconstructs a Figure 6(b)-style spatial view from one Basilisk simulation:
#
#   - coating centre-of-mass trajectory;
#   - tracked maximum-thickness trajectory;
#   - final saved liquid interface;
#   - unit-radius cylinder.
#
# Usage:
#   python3 plot_com_trajectory.py
#   python3 plot_com_trajectory.py --level 9
#   python3 plot_com_trajectory.py --save-only --no-tex
#   python3 plot_com_trajectory.py --output-root output
#
# Requires:
#   postprocess_common.py in the same directory
#   NumPy
#   Matplotlib
#   Pylustrator, unless --save-only is used
# -----------------------------------------------------------------------------

"""Centre-of-mass and maximum-thickness trajectories for one resolution."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
import numpy as np

from postprocess_common import (
    Case,
    TrackingOptions,
    apply_publication_style,
    base_parser,
    load_spatial,
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

DEFAULT_LEVEL = 9
COMPONENT_ID = 0
TRACKING = TrackingOptions()

OUTPUT_NAME = "centre_of_mass_trajectory"

COM_COLOUR = "#8B1E3F"
MAXIMUM_COLOUR = "#173F5F"
INTERFACE_COLOUR = "0.05"


# -----------------------------------------------------------------------------
# Command-line configuration
# -----------------------------------------------------------------------------

parser = base_parser(__doc__)
parser.add_argument(
    "--level",
    type=int,
    default=DEFAULT_LEVEL,
    help=f"maximum AMR level; default: {DEFAULT_LEVEL}",
)
args = parser.parse_args()

OUTPUT_ROOT = resolve_output_root(PROJECT_DIR, args.output_root)


# -----------------------------------------------------------------------------
# Plotting setup and spatial reconstruction
# -----------------------------------------------------------------------------

start_plotting(edit=not args.save_only)
apply_publication_style(
    use_tex=not args.no_tex,
    dpi=args.dpi,
)

result = load_spatial(
    OUTPUT_ROOT,
    CASE,
    args.level,
    component_id=COMPONENT_ID,
    tracking=TRACKING,
)


# -----------------------------------------------------------------------------
# Figure construction
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(
    num=1,
    clear=True,
    figsize=(5.2, 5.2),
)
ax.set_label("main_axes")

# Highlight the converged coating shape.
ax.fill(
    result.final_polygon[:, 0],
    result.final_polygon[:, 1],
    facecolor="0.93",
    edgecolor="none",
    zorder=1,
)

# Draw the cylinder below the trajectories so the CoM remains visible.
ax.add_patch(
    Circle(
        (0.0, 0.0),
        radius=1.0,
        facecolor="0.82",
        edgecolor="0.05",
        linewidth=1.5,
        zorder=2,
    )
)

# Mark the cylinder radius without obscuring the physical trajectories.
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
    zorder=3,
)
ax.text(
    0.52,
    0.06,
    r"$R=1$",
    ha="center",
    va="bottom",
    zorder=3,
)

# Draw the final interface and the two spatial trajectories.
ax.plot(
    result.final_polygon[:, 0],
    result.final_polygon[:, 1],
    color=INTERFACE_COLOUR,
    linewidth=1.8,
    zorder=5,
)
ax.plot(
    result.com_x,
    result.com_y,
    color=COM_COLOUR,
    linewidth=2.0,
    zorder=7,
)
ax.plot(
    result.maximum_x,
    result.maximum_y,
    color=MAXIMUM_COLOUR,
    linewidth=1.8,
    zorder=7,
)

# Mark the initial CoM and the final points of both trajectories.
ax.plot(
    0.0,
    0.0,
    "o",
    color=COM_COLOUR,
    markersize=4.0,
    zorder=8,
)
ax.plot(
    result.com_x[-1],
    result.com_y[-1],
    "o",
    color=COM_COLOUR,
    markersize=5.0,
    zorder=8,
)
ax.plot(
    result.maximum_x[-1],
    result.maximum_y[-1],
    "o",
    color=MAXIMUM_COLOUR,
    markersize=5.0,
    zorder=8,
)


# -----------------------------------------------------------------------------
# Spatial scaling, labels and grid
# -----------------------------------------------------------------------------

all_x = np.concatenate((
    result.final_points[:, 0],
    result.com_x,
    result.maximum_x,
))
all_y = np.concatenate((
    result.final_points[:, 1],
    result.com_y,
    result.maximum_y,
))

extent = max(
    np.max(np.abs(all_x)),
    np.max(np.abs(all_y)),
    1.0,
)
margin = 0.10*extent

ax.set_xlim(-extent - margin, extent + margin)
ax.set_ylim(-extent - margin, extent + margin)
ax.set_aspect("equal", adjustable="box")

ax.set_xlabel(r"$x$", fontsize=14)
ax.set_ylabel(r"$y$", fontsize=14)
ax.set_title(
    rf"$c_R={CASE.film_radius:g},\quad "
    rf"c_V={CASE.cylinder_velocity:g},\quad "
    rf"L={args.level},\quad "
    rf"t={result.final_time:g}$"
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
# Diagnostic legend
# -----------------------------------------------------------------------------

legend = ax.legend(
    handles=[
        Line2D(
            [0],
            [0],
            color=COM_COLOUR,
            linewidth=2.0,
            label="Centre of mass",
        ),
        Line2D(
            [0],
            [0],
            color=MAXIMUM_COLOUR,
            linewidth=1.8,
            label="Maximum film thickness",
        ),
        Line2D(
            [0],
            [0],
            color=INTERFACE_COLOUR,
            linewidth=1.8,
            label="Final interface",
        ),
    ],
    frameon=True,
    framealpha=1.0,
    facecolor="white",
    edgecolor="0.25",
    loc="upper left",
)

fig.tight_layout()


# -----------------------------------------------------------------------------
# Interactive editing and export
# -----------------------------------------------------------------------------

# Pylustrator writes its generated Matplotlib commands immediately above
# this call when Ctrl+S is pressed. Keep this location unobstructed.
if not args.save_only:
    #% start: automatic generated code from pylustrator
    fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}
    import matplotlib as mpl
    getattr(fig, '_pylustrator_init', lambda: ...)()
    fig.ax_dict["main_axes"].legend(loc=(0.05493, 0.8179))
    #% end: automatic generated code from pylustrator
    plt.show()

output = PROJECT_DIR / OUTPUT_NAME
save_figure(
    fig,
    output,
    dpi=args.dpi,
)


# -----------------------------------------------------------------------------
# Terminal summary
# -----------------------------------------------------------------------------

print(f"Final saved interface: {result.final_file}")
print(
    f"Final CoM: "
    f"x={result.com_x[-1]:.10g}, "
    f"y={result.com_y[-1]:.10g}"
)
