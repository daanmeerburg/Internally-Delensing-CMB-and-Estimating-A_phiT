#!/usr/bin/env bash
set -euo pipefail

# Create a clean PR4 test runtime without touching the PR3 runtime.
#
# This script:
#  - creates a dedicated runtime root (INPUT/PLENS/KFIELD)
#  - links cmb_*.fits and noise_*.fits from a PR3 runtime INPUT (for fast data-only PR4 test)
#  - links PR4 lensing products into KFIELD
#  - links a user-provided PR4/NPIPE data map as INPUT/SMICA.fits
#
# It does NOT overwrite existing links/files unless --force is used.

usage() {
  cat <<USAGE
Usage:
  $(basename "$0") \\
    --pr3-runtime-root /scratch/.../Delensing \\
    --pr4-runtime-root /scratch/.../Delensing_PR4test \\
    --pr4-smica /scratch/.../your_pr4_data_map.fits \\
    [--pr4-lensing-root /scratch/hb-CosmoGroup/PR4_Lensing] \\
    [--force]

Notes:
  - Keep PR3 and PR4 runtime roots different.
  - For full PR4 MC consistency you will later replace cmb_*.fits/noise_*.fits too.
USAGE
}

PR3_ROOT=""
PR4_ROOT=""
PR4_SMICA=""
PR4_LENSING_ROOT="/scratch/hb-CosmoGroup/PR4_Lensing"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr3-runtime-root) PR3_ROOT="$2"; shift 2 ;;
    --pr4-runtime-root) PR4_ROOT="$2"; shift 2 ;;
    --pr4-smica) PR4_SMICA="$2"; shift 2 ;;
    --pr4-lensing-root) PR4_LENSING_ROOT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$PR3_ROOT" || -z "$PR4_ROOT" || -z "$PR4_SMICA" ]]; then
  usage
  exit 2
fi

PR3_INPUT="$PR3_ROOT/INPUT"
PR4_INPUT="$PR4_ROOT/INPUT"
PR4_PLENS="$PR4_ROOT/PLENS"
PR4_KFIELD="$PR4_ROOT/KFIELD"

[[ -d "$PR3_INPUT" ]] || { echo "Missing PR3 INPUT dir: $PR3_INPUT" >&2; exit 1; }
[[ -f "$PR4_SMICA" ]] || { echo "Missing PR4 data map: $PR4_SMICA" >&2; exit 1; }
[[ -d "$PR4_LENSING_ROOT" ]] || { echo "Missing PR4 lensing root: $PR4_LENSING_ROOT" >&2; exit 1; }

mkdir -p "$PR4_INPUT" "$PR4_PLENS" "$PR4_KFIELD"

safe_link() {
  local src="$1"
  local dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      rm -f "$dst"
    else
      echo "Skip existing: $dst"
      return 0
    fi
  fi
  ln -s "$src" "$dst"
}

# Link PR3 sims for fast PR4 data-only test.
for f in "$PR3_INPUT"/cmb_*.fits "$PR3_INPUT"/noise_*.fits; do
  [[ -e "$f" ]] || continue
  safe_link "$f" "$PR4_INPUT/$(basename "$f")"
done

# Link PR4 data map.
safe_link "$PR4_SMICA" "$PR4_INPUT/SMICA.fits"

# Link PR4 lensing K-field inputs using klm_000.fits naming expected by current pipeline.
# We map PR4_sims/klm_sim_0000_p.fits -> KFIELD/klm_000.fits, etc.
for i in $(seq 0 599); do
  src="$PR4_LENSING_ROOT/PR4_sims/klm_sim_$(printf '%04d' "$i")_p.fits"
  [[ -f "$src" ]] || continue
  dst="$PR4_KFIELD/klm_$(printf '%03d' "$i").fits"
  safe_link "$src" "$dst"
done

# Also expose a PR4 data kappa map for manual checks.
if [[ -f "$PR4_LENSING_ROOT/PR4_klm_dat_p.fits" ]]; then
  safe_link "$PR4_LENSING_ROOT/PR4_klm_dat_p.fits" "$PR4_KFIELD/klm_dat_pr4_p.fits"
fi

cat <<ENV

PR4 runtime prepared:
  INPUT  = $PR4_INPUT
  PLENS  = $PR4_PLENS
  KFIELD = $PR4_KFIELD

To run in PR4 test mode:
  export PLENS="$PR4_PLENS"
  export INPUT="$PR4_INPUT"
  export KFIELD="$PR4_KFIELD"
  export PARAMS="/home3/p283342/Delensing/clean-delensing/input"

ENV
