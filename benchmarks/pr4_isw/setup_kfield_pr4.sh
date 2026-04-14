#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  $(basename "$0") --variant pr4|pr42018like --dest /scratch/.../KFIELD_PR4 [options]

Options:
  --variant VALUE     Either 'pr4' or 'pr42018like'
  --qe-key VALUE      QE key for pr42018like: p, ptt, or p_p (default: p)
  --dest PATH         Destination KFIELD adapter directory
  --root PATH         PR4 lensing product root (default: /scratch/hb-CosmoGroup/PR4_Lensing)
  --force             Replace existing links in destination

Notes:
  - The adapter exposes the data map as klm_-01.fits because the current
    pipeline uses idx=-1 for data.
  - Simulations are exposed with the original integer indices, e.g.
    klm_060.fits, klm_061.fits, ...
USAGE
}

ROOT="/scratch/hb-CosmoGroup/PR4_Lensing"
VARIANT=""
QE_KEY="p"
DEST=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --variant) VARIANT="$2"; shift 2 ;;
    --qe-key) QE_KEY="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$VARIANT" || -z "$DEST" ]]; then
  usage
  exit 2
fi

case "$VARIANT" in
  pr4)
    [[ "$QE_KEY" == "p" ]] || { echo "Variant 'pr4' only supports --qe-key p" >&2; exit 2; }
    DATA_SRC="$ROOT/PR4_klm_dat_p.fits"
    SIM_DIR="$ROOT/PR4_sims"
    ;;
  pr42018like)
    DATA_SRC="$ROOT/PR42018like_klm_dat_${QE_KEY}.fits"
    SIM_DIR="$ROOT/PR42018like_sims"
    ;;
  *)
    echo "Unsupported variant: $VARIANT" >&2
    exit 2
    ;;
esac

[[ -d "$ROOT" ]] || { echo "Missing PR4 root: $ROOT" >&2; exit 1; }
[[ -f "$DATA_SRC" ]] || { echo "Missing data file: $DATA_SRC" >&2; exit 1; }
[[ -d "$SIM_DIR" ]] || { echo "Missing simulation dir: $SIM_DIR" >&2; exit 1; }

mkdir -p "$DEST"

safe_link() {
  local src="$1"
  local dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      rm -f "$dst"
    else
      return 0
    fi
  fi
  ln -s "$src" "$dst"
}

safe_link "$DATA_SRC" "$DEST/klm_-01.fits"
safe_link "$DATA_SRC" "$DEST/klm_dat.fits"

count=0
for src in "$SIM_DIR"/klm_sim_*_"$QE_KEY".fits; do
  [[ -f "$src" ]] || continue
  idx=$(basename "$src")
  idx=${idx#klm_sim_}
  idx=${idx%_"$QE_KEY".fits}
  idx=$((10#$idx))
  safe_link "$src" "$DEST/klm_$(printf '%03d' "$idx").fits"
  count=$((count + 1))
done

cat <<EOF
Prepared KFIELD adapter:
  dest    = $DEST
  variant = $VARIANT
  qe_key  = $QE_KEY
  sims    = $count
  data    = $DATA_SRC

Use with:
  export KFIELD="$DEST"
EOF
