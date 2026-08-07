#!/bin/sh

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# Optimised single-run driver for CoatedCylinder.c
#
# Default mode retains the established observability outputs:
#   - stdout.log / stderr.log
#   - time.txt                  GNU time summary
#   - event-profile.txt         TRACE=2 cumulative Basilisk profile
#   - perfs                     solver and throughput time series
#   - perf-stat.csv             optional Linux hardware counters
#   - metadata.txt
#
# Usage:
#   sh run_cylinder.sh
#
# Common overrides:
#   FRADIUS=1.5 CV=1.0 MAX_LEVEL=10 sh run_cylinder.sh
#   OMP_NUM_THREADS=6 sh run_cylinder.sh
#   TRACE_LEVEL=0 USE_PERF=0 sh run_cylinder.sh   # lean production timing
#
# The default compiler flags use the local CPU instruction set. The executable
# is therefore intended to run on the same machine on which it is compiled.

set -eu

: "${BASILISK:?BASILISK must point to the Basilisk source directory}"

FRADIUS="${FRADIUS:-1.5}"
CV="${CV:-1.0}"
MAX_LEVEL="${MAX_LEVEL:-10}"
OUTDIR="${OUTDIR:-output}"
USE_PERF="${USE_PERF:-auto}"
TRACE_LEVEL="${TRACE_LEVEL:-2}"

SRC="${SRC:-CoatedCylinder.c}"
EXE="${EXE:-CoatedCylinder}"

# Conservative release optimisation: no fast-math or floating-point
# reassociation. OPT_FLAGS is intentionally word-split by qcc below.
OPT_FLAGS="${OPT_FLAGS:--O3 -fno-fast-math -ffp-contract=off -g0}"
WARN_FLAGS="${WARN_FLAGS:--w}"

# Keep the established four-thread default for direct comparison, while making
# physical-core tests explicit and easy (e.g. OMP_NUM_THREADS=6).
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export OMP_DYNAMIC="${OMP_DYNAMIC:-false}"
export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"

case "$TRACE_LEVEL" in
  0|2) ;;
  *)
    echo "Error: TRACE_LEVEL must be 0 or 2." >&2
    exit 1
    ;;
esac

case "$OUTDIR" in
  ""|"/"|"."|"..")
    echo "Error: refusing unsafe OUTDIR='$OUTDIR'." >&2
    exit 1
    ;;
esac

# Start from one clean output directory.
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR/Interfaces" "$OUTDIR/Animations" "$OUTDIR/Slices"

# qcc translates the Basilisk source to one C translation unit. -O3 and
# -march=native optimise that unit for this machine; strict floating-point
# semantics are retained explicitly. TRACE_LEVEL=2 preserves event profiling.
qcc $OPT_FLAGS $WARN_FLAGS -fopenmp "-DTRACE=$TRACE_LEVEL" \
    "$SRC" -lm -o "$OUTDIR/$EXE" \
    -L"$BASILISK/gl" -lglutils -lfb_tiny

# Prevent perfs.h from opening an interactive gnuplot window in batch runs.
unset DISPLAY || true

{
  echo "project=coated-cylinder"
  echo "date=$(date -Iseconds)"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -srmo)"
  echo "omp_num_threads=$OMP_NUM_THREADS"
  echo "omp_dynamic=$OMP_DYNAMIC"
  echo "omp_proc_bind=$OMP_PROC_BIND"
  echo "omp_places=$OMP_PLACES"
  echo "fRadius=$FRADIUS"
  echo "cV=$CV"
  echo "MAX_LEVEL=$MAX_LEVEL"
  echo "trace_level=$TRACE_LEVEL"
  echo "use_perf=$USE_PERF"
  echo "opt_flags=$OPT_FLAGS"
  echo "compiler=$(cc --version 2>/dev/null | sed -n '1p')"
  if command -v sha256sum >/dev/null 2>&1; then
    echo "source_sha256=$(sha256sum "$SRC" | awk '{print $1}')"
  fi
} > "$OUTDIR/metadata.txt"

# Decide whether perf stat can be used before starting the long simulation.
PERF_OK=0
case "$USE_PERF" in
  0|no|false)
    PERF_OK=0
    ;;
  1|yes|true)
    if ! command -v perf >/dev/null 2>&1; then
      echo "Error: USE_PERF=1 but perf is not installed." >&2
      exit 1
    fi
    if ! perf stat -e task-clock -- true >/dev/null 2>&1; then
      echo "Error: USE_PERF=1 but perf counters are not accessible." >&2
      exit 1
    fi
    PERF_OK=1
    ;;
  auto)
    if command -v perf >/dev/null 2>&1 &&
       perf stat -e task-clock -- true >/dev/null 2>&1; then
      PERF_OK=1
    fi
    ;;
  *)
    echo "Error: USE_PERF must be auto, 0 or 1." >&2
    exit 1
    ;;
esac

# Disable immediate shell termination temporarily so a failed simulation still
# leaves its logs, extracted profile and correct exit-status.txt.
set +e
(
  cd "$OUTDIR"

  if [ "$PERF_OK" -eq 1 ]; then
    /usr/bin/time -v -o time.txt \
      perf stat -x, -o perf-stat.csv \
        -e task-clock,context-switches,cpu-migrations,page-faults \
        -e cycles,instructions,branches,branch-misses \
        -e cache-references,cache-misses \
        -- "./$EXE" "$FRADIUS" "$CV" "$MAX_LEVEL" \
        > stdout.log 2> stderr.log
  else
    /usr/bin/time -v -o time.txt \
      "./$EXE" "$FRADIUS" "$CV" "$MAX_LEVEL" \
      > stdout.log 2> stderr.log
  fi
  RUN_STATUS=$?

  if [ "$TRACE_LEVEL" -eq 2 ]; then
    awk '
      /^[[:space:]]*calls[[:space:]]+total[[:space:]]+self/ { capture = 1 }
      capture { print }
    ' stdout.log stderr.log > event-profile.txt
  else
    : > event-profile.txt
  fi

  printf '%s\n' "$RUN_STATUS" > exit-status.txt
  exit "$RUN_STATUS"
)
RUN_STATUS=$?
set -e

if [ "$RUN_STATUS" -eq 0 ]; then
  echo "Optimised run completed successfully: $OUTDIR"
else
  echo "Run failed with exit status $RUN_STATUS: $OUTDIR" >&2
fi

exit "$RUN_STATUS"
