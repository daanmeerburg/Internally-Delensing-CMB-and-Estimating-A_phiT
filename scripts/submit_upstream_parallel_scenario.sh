#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Submit one scenario through upstream stages with Slurm dependencies:
  qlms(array) -> mf -> qcls(array) -> phi_t

Usage:
  submit_upstream_parallel_scenario.sh --scenario N --runtime-root PATH --venv-activate PATH [options]

Options:
  --scenario N            Scenario index from run_single_scenario.py (required)
  --runtime-root PATH     Runtime root with PLENS/INPUT/KFIELD (required)
  --venv-activate PATH    Virtualenv activate script (required)
  --partition NAME        Slurm partition (default: regularmedium)
  --time-chunk TIME       Walltime for qlms/qcls chunks (default: 08:00:00)
  --time-mf TIME          Walltime for MF stage (default: 04:00:00)
  --time-pt TIME          Walltime for phi_t stage (default: 04:00:00)
  --mem MEM               Memory per job (default: 12G)
  --bias-chunk N          Bias sims per qlms chunk (default: 30)
  --var-chunk N           Var sims per qcls chunk (default: 60)
  --bias-total N          Total bias sims in this scenario (default: 60)
  --var-total N           Total variance sims in this scenario (default: 240)
  --var-base-start N      Starting offset in mc_sims_var (default: 0)
  --skip-phi-t            Submit only qlms/mf/qcls
  --dry-run               Print sbatch commands without submitting
  -h, --help              Show this help
EOF
}

SCENARIO=""
RUNTIME_ROOT=""
VENV_ACTIVATE=""
PARTITION="regularmedium"
TIME_CHUNK="08:00:00"
TIME_MF="04:00:00"
TIME_PT="04:00:00"
MEM="12G"
BIAS_CHUNK=30
VAR_CHUNK=60
BIAS_TOTAL=60
VAR_TOTAL=240
VAR_BASE_START=0
SKIP_PHI_T=0
DRY_RUN=0
FAKE_JOB_ID=910000
LAST_JOB_ID=""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SLURM_FILE="${REPO_ROOT}/run_single_scenario.slurm"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --runtime-root) RUNTIME_ROOT="$2"; shift 2 ;;
    --venv-activate) VENV_ACTIVATE="$2"; shift 2 ;;
    --partition) PARTITION="$2"; shift 2 ;;
    --time-chunk) TIME_CHUNK="$2"; shift 2 ;;
    --time-mf) TIME_MF="$2"; shift 2 ;;
    --time-pt) TIME_PT="$2"; shift 2 ;;
    --mem) MEM="$2"; shift 2 ;;
    --bias-chunk) BIAS_CHUNK="$2"; shift 2 ;;
    --var-chunk) VAR_CHUNK="$2"; shift 2 ;;
    --bias-total) BIAS_TOTAL="$2"; shift 2 ;;
    --var-total) VAR_TOTAL="$2"; shift 2 ;;
    --var-base-start) VAR_BASE_START="$2"; shift 2 ;;
    --skip-phi-t) SKIP_PHI_T=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$SCENARIO" || -z "$RUNTIME_ROOT" || -z "$VENV_ACTIVATE" ]]; then
  usage
  exit 2
fi

submit_parsable() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "DRY-RUN: $*" >&2
    FAKE_JOB_ID=$((FAKE_JOB_ID + 1))
    LAST_JOB_ID="${FAKE_JOB_ID}"
    return 0
  fi
  LAST_JOB_ID="$("$@")"
}

if [[ "$BIAS_TOTAL" -le 0 || "$VAR_TOTAL" -le 0 ]]; then
  echo "Invalid scenario sizes: bias=${BIAS_TOTAL}, var=${VAR_TOTAL}" >&2
  exit 1
fi

if [[ "$VAR_BASE_START" -ge "$VAR_TOTAL" ]]; then
  echo "var-base-start ${VAR_BASE_START} is out of range for var_total ${VAR_TOTAL}" >&2
  exit 1
fi

VAR_REMAIN=$((VAR_TOTAL - VAR_BASE_START))
BIAS_TASKS=$(((BIAS_TOTAL + BIAS_CHUNK - 1) / BIAS_CHUNK))
VAR_TASKS=$(((VAR_REMAIN + VAR_CHUNK - 1) / VAR_CHUNK))

echo "Scenario        : ${SCENARIO}"
echo "Bias sims total : ${BIAS_TOTAL} (chunk ${BIAS_CHUNK} -> ${BIAS_TASKS} tasks)"
echo "Var sims total  : ${VAR_TOTAL} (start ${VAR_BASE_START}, chunk ${VAR_CHUNK} -> ${VAR_TASKS} tasks)"
echo "Partition       : ${PARTITION}"
echo "Dry-run         : ${DRY_RUN}"

submit_parsable sbatch --parsable \
  --array="0-$((BIAS_TASKS - 1))" \
  --partition "${PARTITION}" --time "${TIME_CHUNK}" --mem "${MEM}" \
  --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",SCENARIO="${SCENARIO}",STAGE=qlms,ARRAY_MODE=bias,BIAS_COUNT="${BIAS_CHUNK}",VAR_COUNT=0,SKIP_PHI_T=1 \
  "${SLURM_FILE}"
job_qlms="${LAST_JOB_ID}"

submit_parsable sbatch --parsable \
  --dependency=afterok:${job_qlms} \
  --partition "${PARTITION}" --time "${TIME_MF}" --mem "${MEM}" \
  --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",SCENARIO="${SCENARIO}",STAGE=mf,BIAS_COUNT=0,VAR_COUNT=0,SKIP_PHI_T=1 \
  "${SLURM_FILE}"
job_mf="${LAST_JOB_ID}"

submit_parsable sbatch --parsable \
  --dependency=afterok:${job_mf} \
  --array="0-$((VAR_TASKS - 1))" \
  --partition "${PARTITION}" --time "${TIME_CHUNK}" --mem "${MEM}" \
  --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",SCENARIO="${SCENARIO}",STAGE=qcls,ARRAY_MODE=var,VAR_BASE_START="${VAR_BASE_START}",VAR_COUNT="${VAR_CHUNK}",BIAS_COUNT=0,SKIP_PHI_T=1 \
  "${SLURM_FILE}"
job_qcls="${LAST_JOB_ID}"

if [[ "${SKIP_PHI_T}" == "0" ]]; then
  submit_parsable sbatch --parsable \
    --dependency=afterok:${job_qcls} \
    --partition "${PARTITION}" --time "${TIME_PT}" --mem "${MEM}" \
    --export=ALL,VENV_ACTIVATE="${VENV_ACTIVATE}",RUNTIME_ROOT="${RUNTIME_ROOT}",SCENARIO="${SCENARIO}",STAGE=phi_t,VAR_START="${VAR_BASE_START}",VAR_COUNT="${VAR_REMAIN}",BIAS_COUNT=0 \
    "${SLURM_FILE}"
  job_pt="${LAST_JOB_ID}"
fi

echo "Submitted jobs:"
echo "  qlms array : ${job_qlms}"
echo "  mf         : ${job_mf}"
echo "  qcls array : ${job_qcls}"
if [[ "${SKIP_PHI_T}" == "0" ]]; then
  echo "  phi_t      : ${job_pt}"
fi
