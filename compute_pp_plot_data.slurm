#!/bin/bash
#SBATCH --job-name=pp-cache
#SBATCH --output=/scratch/hb-CosmoGroup/Delensing/logs/pp_cache_%j.out
#SBATCH --error=/scratch/hb-CosmoGroup/Delensing/logs/pp_cache_%j.err
#SBATCH --partition=regularmedium
#SBATCH --time=1-00:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=12G

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

OUTPUT_DIR="${OUTPUT_DIR:-/home3/p283342/Delensing/clean-delensing/THESIS/cache/pp_results}"
STAGE="${STAGE:-all}"
SCENARIO="${SCENARIO:-}"

cd /home3/p283342/Delensing/clean-delensing
mkdir -p /scratch/hb-CosmoGroup/Delensing/logs

ARGS=(
  --stage "${STAGE}"
  --output-dir "${OUTPUT_DIR}"
)

if [[ -n "${SCENARIO}" ]]; then
  ARGS+=(--scenario "${SCENARIO}")
fi

python -u compute_pp_plot_data.py "${ARGS[@]}"
