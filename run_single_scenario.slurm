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
REPO_ROOT="${REPO_ROOT:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
REPO_ROOT="$(cd "${REPO_ROOT}" && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-/path/to/your/runtime-root}"
export PLENS="${PLENS:-$RUNTIME_ROOT/PLENS}"
export INPUT="${INPUT:-$RUNTIME_ROOT/INPUT}"
export PARAMS="${PARAMS:-$REPO_ROOT/input}"
export KFIELD="${KFIELD:-$RUNTIME_ROOT/KFIELD}"

SCENARIO="${SCENARIO:-0}"
BIAS_COUNT="${BIAS_COUNT:-2}"
BIAS_START="${BIAS_START:-0}"
VAR_START="${VAR_START:-0}"
VAR_COUNT="${VAR_COUNT:-5}"
SKIP_PHI_T="${SKIP_PHI_T:-0}"
STAGE="${STAGE:-all}"
ARRAY_MODE="${ARRAY_MODE:-none}"  # none|bias|var
VAR_BASE_START="${VAR_BASE_START:-0}"
MF_USE_BIAS_SLICE="${MF_USE_BIAS_SLICE:-0}"

if [[ "${ARRAY_MODE}" == "bias" && -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
  BIAS_START=$(( SLURM_ARRAY_TASK_ID * BIAS_COUNT ))
  echo "Resolved bias chunk: task ${SLURM_ARRAY_TASK_ID} -> bias_start ${BIAS_START}, bias_count ${BIAS_COUNT}"
fi
if [[ "${ARRAY_MODE}" == "var" && -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
  VAR_START=$(( VAR_BASE_START + SLURM_ARRAY_TASK_ID * VAR_COUNT ))
  echo "Resolved var chunk: task ${SLURM_ARRAY_TASK_ID} -> var_start ${VAR_START}, var_count ${VAR_COUNT}"
fi

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/logs"

ARGS=(
  --scenario "${SCENARIO}"
  --stage "${STAGE}"
  --bias-start "${BIAS_START}"
  --bias-count "${BIAS_COUNT}"
  --var-start "${VAR_START}"
  --var-count "${VAR_COUNT}"
)

if [[ "${SKIP_PHI_T}" == "1" ]]; then
  ARGS+=(--skip-phi-t)
fi
if [[ "${MF_USE_BIAS_SLICE}" == "1" ]]; then
  ARGS+=(--mf-use-bias-slice)
fi

python -u run_single_scenario.py "${ARGS[@]}"
