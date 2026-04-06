#!/bin/bash
#SBATCH --job-name=mf-null
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --partition=regularmedium
#SBATCH --time=1-00:00:00
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
export PLENS="${PLENS:-$RUNTIME_ROOT/PLENS}"
export INPUT="${INPUT:-$RUNTIME_ROOT/INPUT}"
export PARAMS="${PARAMS:-$REPO_ROOT/input}"
export KFIELD="${KFIELD:-$RUNTIME_ROOT/KFIELD}"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/THESIS/cache/amplitude_results}"
GROUP="${GROUP:-noiseless}"
BIN_TYPE="${BIN_TYPE:-agr2}"
EVAL_START="${EVAL_START:-60}"
EVAL_STOP="${EVAL_STOP:-300}"

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/logs"

python -u compute_nulltest_mf_diagnostics.py \
  --group "$GROUP" \
  --bin-type "$BIN_TYPE" \
  --output-dir "$OUTPUT_DIR" \
  --eval-start "$EVAL_START" \
  --eval-stop "$EVAL_STOP"

