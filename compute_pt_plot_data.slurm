#!/bin/bash
#SBATCH --job-name=pt-cache
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-/path/to/your/runtime-root}"
export PLENS="${PLENS:-$RUNTIME_ROOT/PLENS}"
export INPUT="${INPUT:-$RUNTIME_ROOT/INPUT}"
export PARAMS="${PARAMS:-$REPO_ROOT/input}"
export KFIELD="${KFIELD:-$RUNTIME_ROOT/KFIELD}"

GROUP="${GROUP:-both}"
BIN_TYPE="${BIN_TYPE:-fullA_10}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/THESIS/cache/pt_results}"

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/logs"

python -u compute_pt_plot_data.py \
  --group "${GROUP}" \
  --bin-type "${BIN_TYPE}" \
  --output-dir "${OUTPUT_DIR}"
