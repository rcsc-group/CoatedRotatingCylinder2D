#!/usr/bin/env python3

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# -----------------------------------------------------------------------------
# Grid-resolution comparison for coating thickness
#
# Reads logvol.dat for several maximum AMR levels and overlays:
#
#   - minimum film thickness, shown with dashed lines;
#   - maximum film thickness, shown with solid lines;
#   - undisturbed initial film thickness.
#
# Resolution is encoded by colour. Two stable custom key panels separate the
# resolution colours from the physical line styles.
#
# Usage:
#   python3 plot_thickness_resolution.py
#   python3 plot_thickness_resolution.py --levels 7 8 9 10 11
#   python3 plot_thickness_resolution.py --save-only --no-tex
#   python3 plot_thickness_resolution.py --output-root output
#
# Requires:
#   postprocess_common.py in the same directory
#   NumPy
#   Matplotlib
#   Pylustrator, unless --save-only is used
# -----------------------------------------------------------------------------

"""Grid-resolution comparison for coating thickness."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from postprocess_common import (
    Case,
    KeyEntry,
    add_key_panel,
    apply_publication_style,
    base_parser,
    load_thickness,
    relative_bounds,
    resolution_colours,
    resolve_output_root,
    save_figure,
    start_plotting,
)


# -----------------------------------------------------------------------------
# User-configurable case and output settings
# -----------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

CASE = Case(
    film_radius_tag="1.5",
    cylinder_velocity_tag="1.0",
)

DEFAULT_LEVELS = [7, 8, 9, 10, 11]
OUTPUT_NAME = "thickness_resolution_comparison"


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
    figsize=(5.6, 3.5),
)
ax.set_label("main_axes")


# -----------------------------------------------------------------------------
# Load and plot each available resolution level
# -----------------------------------------------------------------------------

loaded = []
maximum_time = 0.0

for level, colour in zip(levels, colours):
    try:
        result = load_thickness(
            OUTPUT_ROOT,
            CASE,
            level,
        )
    except FileNotFoundError as error:
        print(f"Skipping L={level}: {error}")
        continue

    loaded.append((level, colour, result))
    maximum_time = max(
        maximum_time,
        float(np.max(result.time)),
    )

    # Use line style for the physical quantity and colour for resolution.
    ax.plot(
        result.time,
        result.minimum,
        color=colour,
        linestyle="--",
        linewidth=1.4,
    )
    ax.plot(
        result.time,
        result.maximum,
        color=colour,
        linestyle="-",
        linewidth=1.4,
    )

    print(
        f"L={level}: "
        f"t_end={result.time[-1]:g}, "
        f"h_min={result.minimum[-1]:.8g}, "
        f"h_max={result.maximum[-1]:.8g}"
    )

if not loaded:
    raise FileNotFoundError(
        "No matching logvol.dat files were found."
    )


# -----------------------------------------------------------------------------
# Axes formatting and initial-thickness reference
# -----------------------------------------------------------------------------

initial_thickness = CASE.film_radius - 1.0

ax.axhline(
    initial_thickness,
    color="0.35",
    linestyle=":",
    linewidth=1.2,
)

ax.set_xlim(0.0, maximum_time)
ax.set_xlabel(r"Nondimensional time, $t$")
ax.set_ylabel(r"Film thickness, $h-1$")
ax.minorticks_on()
ax.set_axisbelow(True)
ax.grid(
    True,
    which="major",
    color="0.85",
    linewidth=0.7,
)
ax.grid(
    True,
    which="minor",
    color="0.92",
    linewidth=0.45,
    linestyle=":",
)

# Complete the main-axes layout before positioning the independent key panels.
fig.tight_layout()


# -----------------------------------------------------------------------------
# Stable quantity and resolution key panels
# -----------------------------------------------------------------------------

quantity_entries = [
    KeyEntry(
        label="Minimum thickness",
        colour="0.15",
        linestyle="--",
    ),
    KeyEntry(
        label="Maximum thickness",
        colour="0.15",
        linestyle="-",
    ),
    KeyEntry(
        label="Initial thickness",
        colour="0.35",
        linestyle=":",
        value=rf"$h_0-1={initial_thickness:g}$",
    ),
]

resolution_entries = [
    KeyEntry(
        label=rf"Level$={level}$",
        colour=colour,
        linewidth=2.0,
    )
    for level, colour, _ in loaded
]

quantity_key_panel = add_key_panel(
    fig,
    relative_bounds(
        ax,
        [0.025, 0.58, 0.50, 0.34],
    ),
    quantity_entries,
    label="quantity_key_panel",
)

resolution_key_panel = add_key_panel(
    fig,
    relative_bounds(
        ax,
        [0.54, 0.58, 0.44, 0.34],
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
