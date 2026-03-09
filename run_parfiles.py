"""
run_parfiles.py

This script processes different parameter configurations and estimators to:
 1. Generate simulated quadratic lensing maps (QLMs) for each bias simulation.
 2. Compute the mean-field QLM map.
 3. Generate simulated power spectra (QCLs) for each variance simulation.
 4. Compute the binned Phi-T cross-spectrum using ffp10_binner_phiT.

Usage:
    python run_parfiles.py
"""

from tqdm import tqdm
import parfiles.noNoise.parfile as par_len
import parfiles.noNoise.parfile_delensed_qest as par_delMV
import parfiles.noNoise.parfile_delensed_PolQEST as par_delPol
import parfiles.Noise.parfile as parNoise_len
import parfiles.Noise.parfile_delensed_qest as parNoise_delMV
import parfiles.Noise.parfile_delensed_PolQEST as parNoise_delPol

# estimator = ""   # for MV
# estimator = "_p" # for polarization only
# estimator = "tt" # for temperature only
from binner_sims import ffp10_binner_phiT

# Define estimator modules and corresponding estimator suffixes to process
list_par_estimators = [
    [par_len, "p"],
    [par_len, "p_p"],
    [par_delMV, "p"],
    [par_delPol, "ptt"],
    [parNoise_len, "p"],
    [parNoise_len, "p_p"],
    [parNoise_delMV, "p"],
    [parNoise_delPol, "ptt"],
]

def run_scenario(par, estimator):
    print("WORKING ON %s parfile, with %s estimator" % (par.TEMP, estimator))

    for idx in tqdm(par.mc_sims_bias, desc=f"{estimator} bias qlms"):
        par.qlms_dd.get_sim_qlm(estimator, idx)

    par.qlms_dd.get_sim_qlm_mf(estimator, par.mc_sims_mf_dd)

    for idx in tqdm(par.mc_sims_var, desc=f"{estimator} variance qcls"):
        par.qcls_ss.get_sim_qcl(estimator, idx)
        par.qcls_dd.get_sim_qcl(estimator, idx)

    ffp10_binner_phiT(estimator, par, "agr2").get_cL_PHI_T()


def main():
    for par, estimator in list_par_estimators:
        run_scenario(par, estimator)


if __name__ == "__main__":
    main()
