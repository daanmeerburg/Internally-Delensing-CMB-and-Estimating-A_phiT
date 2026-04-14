#!/bin/bash
#SBATCH --job-name=pr4-delens-val
#SBATCH --partition=regularmedium
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=12G
#SBATCH --output=/scratch/hb-CosmoGroup/Delensing/logs/pr4_delens_validation_%j.out
#SBATCH --error=/scratch/hb-CosmoGroup/Delensing/logs/pr4_delens_validation_%j.err

set -euo pipefail

source /home3/p283342/delens-env/bin/activate

export INPUT="${INPUT:-/scratch/hb-CosmoGroup/Delensing_PR4test/INPUT}"
export PLENS="${PLENS:-/scratch/hb-CosmoGroup/Delensing_PR4ext/PLENS}"
export KFIELD="${KFIELD:-/scratch/hb-CosmoGroup/KFIELD_PR4_MV}"
export PARAMS="${PARAMS:-/home3/p283342/Delensing/clean-delensing/input}"

cd /home3/p283342/Delensing/clean-delensing

python /home3/p283342/Delensing/clean-delensing/benchmarks/pr4_isw/validate_external_delensing.py
