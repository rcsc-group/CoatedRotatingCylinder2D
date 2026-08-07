#!/usr/bin/env python3

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# -----------------------------------------------------------------------------
# Single-resolution coating-thickness history
#
# Reads logvol.dat for one coated-cylinder simulation and plots:
#
#   - minimum film thickness;
#   - maximum film thickness;
#   - undisturbed initial film thickness.
#
# The default mode opens Pylustrator for final interactive editing. Press
# Ctrl+S to write graphical changes into this file, then close the window to
# export PDF and 600 dpi PNG versions.
#
# Usage:
#   python3 plot_thickness.py
#   python3 plot_thickness.py --level 10
#   python3 plot_thickness.py --save-only --no-tex
#   python3 plot_thickness.py --output-root output
#
# Requires:
#   postprocess_common.py in the same directory
#   NumPy
#   Matplotlib
#   Pylustrator, unless --save-only is used
# -----------------------------------------------------------------------------

"""Single-resolution coating-thickness history."""

from pathlib import Path

import matplotlib.pyplot as plt

from postprocess_common import (
    Case,
    apply_publication_style,
    base_parser,
    load_thickness,
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

DEFAULT_LEVEL = 10
OUTPUT_NAME = "thickness_evolution"


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
# Plotting setup and data loading
# -----------------------------------------------------------------------------

start_plotting(edit=not args.save_only)
apply_publication_style(
    use_tex=not args.no_tex,
    dpi=args.dpi,
)

result = load_thickness(
    OUTPUT_ROOT,
    CASE,
    args.level,
)

initial_thickness = CASE.film_radius - 1.0


# -----------------------------------------------------------------------------
# Figure construction
# -----------------------------------------------------------------------------

fig, ax = plt.subplots(
    num=1,
    clear=True,
    figsize=(5.2, 3.2),
)
ax.set_label("main_axes")

# Plot the film-thickness extrema and the undisturbed reference value.
ax.plot(
    result.time,
    result.minimum,
    color="0.5",
    linewidth=1.5,
    label="Minimum thickness",
)
ax.plot(
    result.time,
    result.maximum,
    color="0.0",
    linewidth=1.5,
    label="Maximum thickness",
)
ax.axhline(
    initial_thickness,
    color="0.25",
    linestyle="--",
    linewidth=1.2,
    label=rf"Initial thickness, $h_0-1={initial_thickness:g}$",
)

# Apply publication labels and consistent major/minor grid lines.
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

# Use a framed legend consistent with the other post-processing figures.
legend = ax.legend(
    frameon=True,
    framealpha=1.0,
    facecolor="white",
    edgecolor="0.25",
    loc="best",
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
    fig.ax_dict["main_axes"].legend(loc=(0.4776, 0.4778))
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

print(
    f"L={args.level}: "
    f"final minimum={result.minimum[-1]:.8g}, "
    f"final maximum={result.maximum[-1]:.8g}"
)
