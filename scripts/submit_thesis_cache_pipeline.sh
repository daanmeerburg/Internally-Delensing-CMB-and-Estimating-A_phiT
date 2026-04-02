#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Submit dependency-chained Slurm jobs for thesis cache generation.

Usage:
  submit_thesis_cache_pipeline.sh [options]

Options:
  --repo-root PATH         Repository root (default: parent of this script)
  --runtime-root PATH      Runtime root containing PLENS/INPUT/KFIELD (required)
  --venv-activate PATH     Virtualenv activate script (required)
  --pipeline NAME          pp | pt | both (default: both)
  --partition NAME         Slurm partition (default: regularmedium)
  --time-pp TIME           Walltime for PP jobs (default: 3-00:00:00)
  --time-pt TIME           Walltime for PT jobs (default: 1-00:00:00)
  --mem-pp MEM             Memory for PP jobs (default: 12G)
  --mem-pt MEM             Memory for PT jobs (default: 8G)
  --dry-run                Print sbatch commands without submitting
  -h, --help               Show this help

Notes:
  - Jobs are submitted with afterok dependencies.
  - Scenario arrays are used for non-baseline scenarios.
  - Baseline scenario is `mv_lensed`; remaining scenarios are run as arrays:
      mv_input_kappa,mv_internal_qest,tt_internal_polqest
EOF
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT=""
VENV_ACTIVATE=""
PIPELINE="both"
PARTITION="regularmedium"
TIME_PP="3-00:00:00"
TIME_PT="1-00:00:00"
MEM_PP="12G"
MEM_PT="8G"
DRY_RUN=0
FAKE_JOB_ID=900000

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --runtime-root) RUNTIME_ROOT="$2"; shift 2 ;;
    --venv-activate) VENV_ACTIVATE="$2"; shift 2 ;;
    --pipeline) PIPELINE="$2"; shift 2 ;;
    --partition) PARTITION="$2"; shift 2 ;;
    --time-pp) TIME_PP="$2"; shift 2 ;;
    --time-pt) TIME_PT="$2"; shift 2 ;;
    --mem-pp) MEM_PP="$2"; shift 2 ;;
    --mem-pt) MEM_PT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$RUNTIME_ROOT" ]]; then
  echo "--runtime-root is required" >&2
  exit 2
fi
if [[ -z "$VENV_ACTIVATE" ]]; then
  echo "--venv-activate is required" >&2
  exit 2
fi
if [[ "$PIPELINE" != "pp" && "$PIPELINE" != "pt" && "$PIPELINE" != "both" ]]; then
  echo "--pipeline must be one of: pp, pt, both" >&2
  exit 2
fi

submit() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY-RUN: $*"
    return 0
  fi
  "$@"
}

LAST_JOB_ID=""
submit_parsable() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY-RUN: $*" >&2
    FAKE_JOB_ID=$((FAKE_JOB_ID + 1))
    LAST_JOB_ID="${FAKE_JOB_ID}"
    return 0
  fi
  LAST_JOB_ID="$("$@")"
}

PP_SLURM="${REPO_ROOT}/compute_pp_plot_data.slurm"
PT_SLURM="${REPO_ROOT}/compute_pt_plot_data.slurm"
SCENARIO_REST="mv_input_kappa,mv_internal_qest,tt_internal_polqest"

echo "Repository root : ${REPO_ROOT}"
echo "Runtime root    : ${RUNTIME_ROOT}"
echo "Pipeline        : ${PIPELINE}"
echo "Partition       : ${PARTITION}"
echo "Dry-run         : ${DRY_RUN}"

if [[ "$PIPELINE" == "pp" || "$PIPELINE" == "both" ]]; then
  echo
  echo "Submitting PP dependency chain..."
  submit_parsable sbatch --parsable \
    --partition "${PARTITION}" --time "${TIME_PP}" --mem "${MEM_PP}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=clpp_noiseless,SCENARIO=mv_lensed \
    "${PP_SLURM}"
  pp_noiseless_seed="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --dependency=afterok:${pp_noiseless_seed} \
    --array=0-2 \
    --partition "${PARTITION}" --time "${TIME_PP}" --mem "${MEM_PP}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=clpp_noiseless,SCENARIO_LIST="${SCENARIO_REST}" \
    "${PP_SLURM}"
  pp_noiseless_rest="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --partition "${PARTITION}" --time "${TIME_PP}" --mem "${MEM_PP}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=clpp_noisy,SCENARIO=mv_lensed \
    "${PP_SLURM}"
  pp_noisy_seed="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --dependency=afterok:${pp_noisy_seed} \
    --array=0-2 \
    --partition "${PARTITION}" --time "${TIME_PP}" --mem "${MEM_PP}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=clpp_noisy,SCENARIO_LIST="${SCENARIO_REST}" \
    "${PP_SLURM}"
  pp_noisy_rest="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --partition "${PARTITION}" --time 02:00:00 --mem 4G \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=validation \
    "${PP_SLURM}"
  pp_validation="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --dependency=afterok:${pp_noiseless_rest}:${pp_noisy_rest} \
    --partition "${PARTITION}" --time "${TIME_PP}" --mem "${MEM_PP}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",STAGE=wf_eff \
    "${PP_SLURM}"
  pp_wf_eff="${LAST_JOB_ID}"

  echo "PP jobs:"
  echo "  noiseless seed : ${pp_noiseless_seed}"
  echo "  noiseless rest : ${pp_noiseless_rest}"
  echo "  noisy seed     : ${pp_noisy_seed}"
  echo "  noisy rest     : ${pp_noisy_rest}"
  echo "  validation     : ${pp_validation}"
  echo "  wf_eff         : ${pp_wf_eff}"
fi

if [[ "$PIPELINE" == "pt" || "$PIPELINE" == "both" ]]; then
  echo
  echo "Submitting PT dependency chain..."
  submit_parsable sbatch --parsable \
    --partition "${PARTITION}" --time "${TIME_PT}" --mem "${MEM_PT}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",GROUP=noiseless,SCENARIO=mv_lensed \
    "${PT_SLURM}"
  pt_noiseless_seed="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --dependency=afterok:${pt_noiseless_seed} \
    --array=0-2 \
    --partition "${PARTITION}" --time "${TIME_PT}" --mem "${MEM_PT}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",GROUP=noiseless,SCENARIO_LIST="${SCENARIO_REST}" \
    "${PT_SLURM}"
  pt_noiseless_rest="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --partition "${PARTITION}" --time "${TIME_PT}" --mem "${MEM_PT}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",GROUP=noisy,SCENARIO=mv_lensed \
    "${PT_SLURM}"
  pt_noisy_seed="${LAST_JOB_ID}"

  submit_parsable sbatch --parsable \
    --dependency=afterok:${pt_noisy_seed} \
    --array=0-2 \
    --partition "${PARTITION}" --time "${TIME_PT}" --mem "${MEM_PT}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",GROUP=noisy,SCENARIO_LIST="${SCENARIO_REST}" \
    "${PT_SLURM}"
  pt_noisy_rest="${LAST_JOB_ID}"

  echo "PT jobs:"
  echo "  noiseless seed : ${pt_noiseless_seed}"
  echo "  noiseless rest : ${pt_noiseless_rest}"
  echo "  noisy seed     : ${pt_noisy_seed}"
  echo "  noisy rest     : ${pt_noisy_rest}"
fi
