#!/bin/bash
#SBATCH --job-name=delens-test
#SBATCH --output=/scratch/hb-CosmoGroup/Delensing/logs/delens_test_%j.out
#SBATCH --error=/scratch/hb-CosmoGroup/Delensing/logs/delens_test_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -euo pipefail

module load GCC/12.3.0
source /home3/p283342/delens-env/bin/activate

export TOOLCHAIN_BIN_GCC="$EBROOTGCCCORE/bin"
export TOOLCHAIN_BIN_BINUTILS="$EBROOTBINUTILS/bin"
export PATH="$TOOLCHAIN_BIN_GCC:$TOOLCHAIN_BIN_BINUTILS:$PATH"

export CC="$TOOLCHAIN_BIN_GCC/gcc"
export CXX="$TOOLCHAIN_BIN_GCC/g++"
export FC="$TOOLCHAIN_BIN_GCC/gfortran"
export F77="$FC"
export F90="$FC"

export PLENS=/scratch/hb-CosmoGroup/Delensing/PLENS
export INPUT=/scratch/hb-CosmoGroup/Delensing/INPUT
export PARAMS=/home3/p283342/Delensing/clean-delensing/input
export KFIELD=/scratch/hb-CosmoGroup/Delensing/KFIELD

SCENARIO="${SCENARIO:-0}"
BIAS_COUNT="${BIAS_COUNT:-2}"
VAR_START="${VAR_START:-0}"
VAR_COUNT="${VAR_COUNT:-5}"
SKIP_PHI_T="${SKIP_PHI_T:-0}"

cd /home3/p283342/Delensing/clean-delensing
mkdir -p /scratch/hb-CosmoGroup/Delensing/logs

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
