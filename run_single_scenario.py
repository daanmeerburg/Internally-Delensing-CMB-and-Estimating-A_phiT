#!/usr/bin/env python3
"""
Run a single delensing scenario, optionally on a reduced set of simulations.

Examples:
    python run_single_scenario.py --scenario 0
    python run_single_scenario.py --scenario 0 --bias-count 2 --var-count 5
    python run_single_scenario.py --scenario 5 --var-start 60 --var-count 10
    python run_single_scenario.py --scenario 5 --stage qlms --bias-start 120 --bias-count 30
    python run_single_scenario.py --scenario 5 --stage mf
    python run_single_scenario.py --scenario 5 --stage qcls --var-start 120 --var-count 60
"""

import argparse
from typing import Iterable, Optional

from tqdm import tqdm

import parfiles.noNoise.parfile as par_len
import parfiles.noNoise.parfile_delensed as par_del_input
import parfiles.noNoise.parfile_delensed_qest as par_del_mv
import parfiles.noNoise.parfile_delensed_PolQEST as par_del_pol
import parfiles.Noise.parfile as par_noise_len
import parfiles.Noise.parfile_delensed as par_noise_del_input
import parfiles.Noise.parfile_delensed_qest as par_noise_del_mv
import parfiles.Noise.parfile_delensed_PolQEST as par_noise_del_pol
from binner_sims import ffp10_binner_phiT


SCENARIOS = [
    (par_len, "p", "noNoise baseline lensed"),
    (par_len, "p_p", "noNoise baseline polarization QE"),
    (par_del_input, "p", "noNoise delensed with input kappa"),
    (par_del_mv, "p", "noNoise internally delensed MV-QEST"),
    (par_del_pol, "ptt", "noNoise internally delensed Pol-QEST"),
    (par_noise_len, "p", "Noise baseline lensed"),
    (par_noise_len, "p_p", "Noise baseline polarization QE"),
    (par_noise_del_input, "p", "Noise delensed with input kappa"),
    (par_noise_del_mv, "p", "Noise internally delensed MV-QEST"),
    (par_noise_del_pol, "ptt", "Noise internally delensed Pol-QEST"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        type=int,
        required=True,
        help="Scenario index in SCENARIOS. Use --list to inspect the available options.",
    )
    parser.add_argument("--list", action="store_true", help="List available scenarios and exit.")
    parser.add_argument("--bias-count", type=int, default=None, help="Number of bias sims to run.")
    parser.add_argument(
        "--bias-start",
        type=int,
        default=0,
        help="Start index inside mc_sims_bias for the bias loop.",
    )
    parser.add_argument(
        "--var-start",
        type=int,
        default=None,
        help="Start index inside mc_sims_var for the variance loop. Default is the beginning.",
    )
    parser.add_argument("--var-count", type=int, default=None, help="Number of variance sims to run.")
    parser.add_argument(
        "--skip-phi-t",
        action="store_true",
        help="Skip the final phi-T binning step. Useful for a very short smoke test.",
    )
    parser.add_argument(
        "--stage",
        choices=("all", "qlms", "mf", "qcls", "phi_t"),
        default="all",
        help="Run only a specific upstream stage.",
    )
    parser.add_argument(
        "--mf-use-bias-slice",
        action="store_true",
        help="Use selected bias sims for mean-field instead of par.mc_sims_mf_dd.",
    )
    return parser.parse_args()


def take_slice(values: Iterable[int], start: Optional[int], count: Optional[int]):
    seq = list(values)
    if start is None:
        start = 0
    end = None if count is None else start + count
    return seq[start:end]


def list_scenarios() -> None:
    for idx, (_, estimator, label) in enumerate(SCENARIOS):
        print(f"{idx}: {label} [{estimator}]")


def run_scenario(
    par,
    estimator,
    label,
    stage,
    bias_start,
    bias_count,
    var_start,
    var_count,
    skip_phi_t,
    mf_use_bias_slice,
) -> None:
    bias_sims = take_slice(par.mc_sims_bias, bias_start, bias_count)
    var_sims = take_slice(par.mc_sims_var, var_start, var_count)
    mf_sims = list(bias_sims) if mf_use_bias_slice else list(par.mc_sims_mf_dd)

    print(f"WORKING ON {label}: {par.TEMP} with estimator {estimator}")
    print(f"bias sims: {bias_sims[0] if bias_sims else 'none'} -> {bias_sims[-1] if bias_sims else 'none'} ({len(bias_sims)})")
    print(f"var sims:  {var_sims[0] if var_sims else 'none'} -> {var_sims[-1] if var_sims else 'none'} ({len(var_sims)})")
    print(f"mf sims:   {mf_sims[0] if mf_sims else 'none'} -> {mf_sims[-1] if mf_sims else 'none'} ({len(mf_sims)})")
    print(f"stage: {stage}")

    if stage in ("all", "qlms"):
        for idx in tqdm(bias_sims, desc=f"{estimator} bias qlms"):
            par.qlms_dd.get_sim_qlm(estimator, idx)

    if stage in ("all", "mf"):
        if mf_sims:
            par.qlms_dd.get_sim_qlm_mf(estimator, mf_sims)
        else:
            print("No mean-field sims selected; skipping MF computation.")

    if stage in ("all", "qcls"):
        for idx in tqdm(var_sims, desc=f"{estimator} variance qcls"):
            par.qcls_ss.get_sim_qcl(estimator, idx)
            par.qcls_dd.get_sim_qcl(estimator, idx)

    if stage in ("all", "phi_t") and not skip_phi_t:
        ffp10_binner_phiT(estimator, par, "agr2").get_cL_PHI_T(mc_sims=var_sims if var_sims else None)


def main() -> None:
    args = parse_args()
    if args.list:
        list_scenarios()
        return

    if args.scenario < 0 or args.scenario >= len(SCENARIOS):
        raise SystemExit(f"Scenario index out of range: {args.scenario}")

    par, estimator, label = SCENARIOS[args.scenario]
    run_scenario(
        par,
        estimator,
        label,
        args.stage,
        args.bias_start,
        args.bias_count,
        args.var_start,
        args.var_count,
        args.skip_phi_t,
        args.mf_use_bias_slice,
    )


if __name__ == "__main__":
    main()
