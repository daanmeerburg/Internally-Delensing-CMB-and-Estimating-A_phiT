#!/bin/bash
#SBATCH --job-name=amp-cache
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --partition=regularmedium
#SBATCH --time=3-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=12G

set -euo pipefail

module load GCC/12.3.0
VENV_ACTIVATE="${VENV_ACTIVATE:-/path/to/your/venv/bin/activate}"
if [ ! -f "$VENV_ACTIVATE" ]; then
  echo "Set VENV_ACTIVATE to your virtualenv activate script before submitting." >&2
  exit 1
fi
source "$VENV_ACTIVATE"

export TOOLCHAIN_BIN_GCC="$EBROOTGCCCORE/bin"
export TOOLCHAIN_BIN_BINUTILS="$EBROOTBINUTILS/bin"
export PATH="$TOOLCHAIN_BIN_GCC:$TOOLCHAIN_BIN_BINUTILS:$PATH"

export CC="$TOOLCHAIN_BIN_GCC/gcc"
export CXX="$TOOLCHAIN_BIN_GCC/g++"
export FC="$TOOLCHAIN_BIN_GCC/gfortran"
export F77="$FC"
export F90="$FC"

REPO_ROOT="${REPO_ROOT:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-/path/to/your/runtime-root}"
REFERENCE_RUNTIME_ROOT="${REFERENCE_RUNTIME_ROOT:-}"
export PLENS="${PLENS:-$RUNTIME_ROOT/PLENS}"
export INPUT="${INPUT:-$RUNTIME_ROOT/INPUT}"
export PARAMS="${PARAMS:-$REPO_ROOT/input}"
export KFIELD="${KFIELD:-$RUNTIME_ROOT/KFIELD}"
if [[ -n "${REFERENCE_RUNTIME_ROOT}" ]]; then
  export DELENSING_REFERENCE_PLENS="${DELENSING_REFERENCE_PLENS:-$REFERENCE_RUNTIME_ROOT/PLENS}"
fi

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/THESIS/cache/amplitude_results}"
REFERENCE_CACHE_DIR="${REFERENCE_CACHE_DIR:-}"
STAGE="${STAGE:-all}"
FORCE="${FORCE:-0}"

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/logs"

ARGS=(
  --stage "${STAGE}"
  --output-dir "${OUTPUT_DIR}"
)

if [[ -n "${REFERENCE_CACHE_DIR}" ]]; then
  ARGS+=(--reference-cache-dir "${REFERENCE_CACHE_DIR}")
fi

if [[ "${FORCE}" == "1" ]]; then
  ARGS+=(--force)
fi

python -u compute_amplitude_plot_data.py "${ARGS[@]}"
