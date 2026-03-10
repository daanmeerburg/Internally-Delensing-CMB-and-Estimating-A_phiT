"""
run_parfiles.py

This script processes the main thesis analysis scenarios by:
 1. Generating simulated quadratic lensing maps (QLMs) for each bias simulation.
 2. Computing the mean-field QLM map.
 3. Generating simulated power spectra (QCLs) for each variance simulation.
 4. Computing the binned Phi-T cross-spectrum using ffp10_binner_phiT.

Scenario matrix covered here:
  - noNoise baseline lensed:                  estimator 'p'
  - noNoise baseline polarization QE:         estimator 'p_p'
  - noNoise delensed with input kappa:        estimator 'p'
  - noNoise internally delensed MV-QEST:      estimator 'p'
  - noNoise internally delensed Pol-QEST:     estimator 'ptt'
  - Noise baseline lensed:                    estimator 'p'
  - Noise baseline polarization QE:           estimator 'p_p'
  - Noise delensed with input kappa:          estimator 'p'
  - Noise internally delensed MV-QEST:        estimator 'p'
  - Noise internally delensed Pol-QEST:       estimator 'ptt'

Usage:
    python run_parfiles.py
"""

from tqdm import tqdm
import parfiles.noNoise.parfile as par_len
import parfiles.noNoise.parfile_delensed as par_delInput
import parfiles.noNoise.parfile_delensed_qest as par_delMV
import parfiles.noNoise.parfile_delensed_PolQEST as par_delPol
import parfiles.Noise.parfile as parNoise_len
import parfiles.Noise.parfile_delensed as parNoise_delInput
import parfiles.Noise.parfile_delensed_qest as parNoise_delMV
import parfiles.Noise.parfile_delensed_PolQEST as parNoise_delPol

# estimator = ""   # for MV
# estimator = "_p" # for polarization only
# estimator = "tt" # for temperature only
from binner_sims import ffp10_binner_phiT

# Define the scenarios needed by the current notebooks and thesis figures.
# Each entry is:
#   (parfile_module, estimator_key, human_readable_label)
SCENARIOS = [
    (par_len, "p", "noNoise baseline lensed"),
    (par_len, "p_p", "noNoise baseline polarization QE"),
    (par_delInput, "p", "noNoise delensed with input kappa"),
    (par_delMV, "p", "noNoise internally delensed MV-QEST"),
    (par_delPol, "ptt", "noNoise internally delensed Pol-QEST"),
    (parNoise_len, "p", "Noise baseline lensed"),
    (parNoise_len, "p_p", "Noise baseline polarization QE"),
    (parNoise_delInput, "p", "Noise delensed with input kappa"),
    (parNoise_delMV, "p", "Noise internally delensed MV-QEST"),
    (parNoise_delPol, "ptt", "Noise internally delensed Pol-QEST"),
]

def run_scenario(par, estimator, label):
    print(f"WORKING ON {label}: {par.TEMP} with estimator {estimator}")

    for idx in tqdm(par.mc_sims_bias, desc=f"{estimator} bias qlms"):
        par.qlms_dd.get_sim_qlm(estimator, idx)

    par.qlms_dd.get_sim_qlm_mf(estimator, par.mc_sims_mf_dd)

    for idx in tqdm(par.mc_sims_var, desc=f"{estimator} variance qcls"):
        par.qcls_ss.get_sim_qcl(estimator, idx)
        par.qcls_dd.get_sim_qcl(estimator, idx)

    ffp10_binner_phiT(estimator, par, "agr2").get_cL_PHI_T()


def main():
    for par, estimator, label in SCENARIOS:
        run_scenario(par, estimator, label)


if __name__ == "__main__":
    main()
