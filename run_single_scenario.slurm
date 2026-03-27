#!/bin/bash
#SBATCH --job-name=delens-test
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --time=02:00:00
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

SCENARIO="${SCENARIO:-0}"
BIAS_COUNT="${BIAS_COUNT:-2}"
VAR_START="${VAR_START:-0}"
VAR_COUNT="${VAR_COUNT:-5}"
SKIP_PHI_T="${SKIP_PHI_T:-0}"

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/logs"

ARGS=(
  --scenario "${SCENARIO}"
  --bias-count "${BIAS_COUNT}"
  --var-start "${VAR_START}"
  --var-count "${VAR_COUNT}"
)

if [[ "${SKIP_PHI_T}" == "1" ]]; then
  ARGS+=(--skip-phi-t)
fi

python -u run_single_scenario.py "${ARGS[@]}"
