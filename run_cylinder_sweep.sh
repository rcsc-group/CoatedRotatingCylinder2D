#!/bin/sh

# Author: Radu Cimpeanu
# Date: 03/08/2026
#
# Optimised parameter-sweep driver for CoatedCylinder.c
#
# FRADIUS, CV and MAX_LEVEL are whitespace-separated lists. The source is
# compiled once, then every combination is run in its own case directory.
#
# Examples:
#
#   # One case
#   TRACE_LEVEL=0 USE_PERF=0 MAX_LEVEL=10 sh run_cylinder_sweep.sh
#
#   # Resolution study
#   TRACE_LEVEL=0 USE_PERF=0 \
#     MAX_LEVEL="7 8 9 10 11" sh run_cylinder_sweep.sh
#
#   # Full Cartesian sweep
#   FRADIUS="1.25 1.5 1.75" \
#   CV="0.5 1.0 1.5" \
#   MAX_LEVEL="8 9 10" \
#     sh run_cylinder_sweep.sh
#
# Output layout:
#
#   output/
#   ├── CoatedCylinder
#   ├── build-metadata.txt
#   ├── sweep-summary.tsv
#   ├── fR_1.5_cV_1.0_L_7/
#   ├── fR_1.5_cV_1.0_L_8/
#   └── ...
#
# Common controls:
#   OMP_NUM_THREADS=4
#   TRACE_LEVEL=2             0 or 2
#   USE_PERF=auto             auto, 0 or 1
#   OUTROOT=output
#
# OUTDIR is retained as a backwards-compatible alias for OUTROOT.

set -eu

: "${BASILISK:?BASILISK must point to the Basilisk source directory}"

FRADIUS_LIST="${FRADIUS:-1.5}"
CV_LIST="${CV:-1.0}"
MAX_LEVEL_LIST="${MAX_LEVEL:-10}"

OUTROOT="${OUTROOT:-${OUTDIR:-output}}"
USE_PERF="${USE_PERF:-auto}"
TRACE_LEVEL="${TRACE_LEVEL:-2}"

SRC="${SRC:-CoatedCylinder.c}"
EXE="${EXE:-CoatedCylinder}"

# Conservative release optimisation. No fast-math or floating-point
# reassociation is enabled.
OPT_FLAGS="${OPT_FLAGS:--O3 -fno-fast-math -ffp-contract=off -g0}"
WARN_FLAGS="${WARN_FLAGS:--w}"

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

case "$OUTROOT" in
  ""|"/"|"."|"..")
    echo "Error: refusing unsafe OUTROOT='$OUTROOT'." >&2
    exit 1
    ;;
esac

[ -n "$FRADIUS_LIST" ] ||
  { echo "Error: FRADIUS must contain at least one value." >&2; exit 1; }
[ -n "$CV_LIST" ] ||
  { echo "Error: CV must contain at least one value." >&2; exit 1; }
[ -n "$MAX_LEVEL_LIST" ] ||
  { echo "Error: MAX_LEVEL must contain at least one value." >&2; exit 1; }

rm -rf "$OUTROOT"
mkdir -p "$OUTROOT"

# Compile once. Every parameter combination uses this same executable.
qcc $OPT_FLAGS $WARN_FLAGS -fopenmp "-DTRACE=$TRACE_LEVEL" \
    "$SRC" -lm -o "$OUTROOT/$EXE" \
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
  echo "fRadius_list=$FRADIUS_LIST"
  echo "cV_list=$CV_LIST"
  echo "MAX_LEVEL_list=$MAX_LEVEL_LIST"
  echo "trace_level=$TRACE_LEVEL"
  echo "use_perf=$USE_PERF"
  echo "opt_flags=$OPT_FLAGS"
  echo "compiler=$(cc --version 2>/dev/null | sed -n '1p')"
  if command -v sha256sum >/dev/null 2>&1; then
    echo "source_sha256=$(sha256sum "$SRC" | awk '{print $1}')"
  fi
} > "$OUTROOT/build-metadata.txt"

# Test perf availability once for the complete sweep.
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

SUMMARY="$OUTROOT/sweep-summary.tsv"
printf "case\tfRadius\tcV\tMAX_LEVEL\texit_status\truptured\n" > "$SUMMARY"

OVERALL_STATUS=0
CASE_COUNT=0

for FRADIUS_VALUE in $FRADIUS_LIST; do
  for CV_VALUE in $CV_LIST; do
    for LEVEL_VALUE in $MAX_LEVEL_LIST; do
      CASE_COUNT=$((CASE_COUNT + 1))
      CASE_NAME="fR_${FRADIUS_VALUE}_cV_${CV_VALUE}_L_${LEVEL_VALUE}"
      CASEDIR="$OUTROOT/$CASE_NAME"

      echo "------------------------------------------------------------"
      echo "Running case $CASE_COUNT:"
      echo "  fRadius         = $FRADIUS_VALUE"
      echo "  cV              = $CV_VALUE"
      echo "  MAX_LEVEL       = $LEVEL_VALUE"
      echo "  OMP_NUM_THREADS = $OMP_NUM_THREADS"
      echo "  output          = $CASEDIR"
      echo "------------------------------------------------------------"

      mkdir -p "$CASEDIR/Interfaces" "$CASEDIR/Animations" "$CASEDIR/Slices"

      {
        echo "project=coated-cylinder"
        echo "date=$(date -Iseconds)"
        echo "case=$CASE_NAME"
        echo "fRadius=$FRADIUS_VALUE"
        echo "cV=$CV_VALUE"
        echo "MAX_LEVEL=$LEVEL_VALUE"
        echo "omp_num_threads=$OMP_NUM_THREADS"
        echo "omp_dynamic=$OMP_DYNAMIC"
        echo "omp_proc_bind=$OMP_PROC_BIND"
        echo "omp_places=$OMP_PLACES"
        echo "trace_level=$TRACE_LEVEL"
        echo "perf_enabled=$PERF_OK"
        echo "opt_flags=$OPT_FLAGS"
      } > "$CASEDIR/metadata.txt"

      set +e
      (
        cd "$CASEDIR"

        if [ "$PERF_OK" -eq 1 ]; then
          /usr/bin/time -v -o time.txt \
            perf stat -x, -o perf-stat.csv \
              -e task-clock,context-switches,cpu-migrations,page-faults \
              -e cycles,instructions,branches,branch-misses \
              -e cache-references,cache-misses \
              -- "../$EXE" "$FRADIUS_VALUE" "$CV_VALUE" "$LEVEL_VALUE" \
              > stdout.log 2> stderr.log
        else
          /usr/bin/time -v -o time.txt \
            "../$EXE" "$FRADIUS_VALUE" "$CV_VALUE" "$LEVEL_VALUE" \
            > stdout.log 2> stderr.log
        fi
        RUN_STATUS=$?

        if [ "$TRACE_LEVEL" -eq 2 ]; then
          awk '
            /^[[:space:]]*calls[[:space:]]+total[[:space:]]+self/ {
              capture = 1
            }
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

      RUPTURED="NA"
      if [ -f "$CASEDIR/rupture.flag" ]; then
        RUPTURED=$(sed -n '1p' "$CASEDIR/rupture.flag")
      fi

      printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$CASE_NAME" "$FRADIUS_VALUE" "$CV_VALUE" "$LEVEL_VALUE" \
        "$RUN_STATUS" "$RUPTURED" >> "$SUMMARY"

      if [ "$RUN_STATUS" -eq 0 ]; then
        echo "Completed successfully: $CASE_NAME"
      else
        echo "Case failed with exit status $RUN_STATUS: $CASE_NAME" >&2
        OVERALL_STATUS="$RUN_STATUS"
      fi
    done
  done
done

echo "------------------------------------------------------------"
echo "Sweep complete: $CASE_COUNT case(s)"
echo "Summary: $SUMMARY"
echo "------------------------------------------------------------"

exit "$OVERALL_STATUS"
