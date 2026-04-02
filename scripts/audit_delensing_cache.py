#!/usr/bin/env python3
"""Quick health checks for delensing runtime caches.

Checks:
- Missing expected PT/PP cache npz files.
- Raw CMB/Noise files with abnormal sizes (truncation heuristic).
- Scenario delensed_sims directories that are partially populated.
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

EXPECTED_PT = [
    "noiseless_fiducial.npz",
    "noiseless_mv_lensed.npz",
    "noiseless_mv_input_kappa.npz",
    "noiseless_mv_internal_qest.npz",
    "noiseless_tt_internal_polqest.npz",
    "noisy_fiducial.npz",
    "noisy_mv_lensed.npz",
    "noisy_mv_input_kappa.npz",
    "noisy_mv_internal_qest.npz",
    "noisy_tt_internal_polqest.npz",
]

EXPECTED_PP = [
    "validation_noiseless_agr2.npz",
    "noiseless_clpp_fiducial_fullA_20.npz",
    "noiseless_clpp_mv_lensed_fullA_20.npz",
    "noiseless_clpp_mv_input_kappa_fullA_20.npz",
    "noiseless_clpp_mv_internal_qest_fullA_20.npz",
    "noiseless_clpp_tt_internal_polqest_fullA_20.npz",
    "noiseless_wf_vs_eff_fullA_10.npz",
    "noisy_clpp_fiducial_fullA_20.npz",
    "noisy_clpp_mv_lensed_fullA_20.npz",
    "noisy_clpp_mv_input_kappa_fullA_20.npz",
    "noisy_clpp_mv_internal_qest_fullA_20.npz",
    "noisy_clpp_tt_internal_polqest_fullA_20.npz",
    "noisy_wf_vs_eff_fullA_10.npz",
]


def list_missing(base: Path, names: List[str]) -> List[str]:
    return [name for name in names if not (base / name).exists()]


def _size_histogram(raw_dir: Path, pattern: str) -> Dict[int, int]:
    hist = {}
    for p in sorted(raw_dir.glob(pattern)):
        s = p.stat().st_size
        hist[s] = hist.get(s, 0) + 1
    return hist


def _modal_size(hist: Dict[int, int]) -> int:
    if not hist:
        return 0
    return max(hist.items(), key=lambda x: x[1])[0]


def check_raw_sizes(raw_dir: Path, pattern: str, expected_size: int = 0) -> Tuple[int, List[Path], Dict[int, int]]:
    hist = _size_histogram(raw_dir, pattern)
    nominal = expected_size if expected_size > 0 else _modal_size(hist)
    bad = []
    for p in sorted(raw_dir.glob(pattern)):
        if p.stat().st_size != nominal:
            bad.append(p)
    return nominal, bad, hist


def delensed_sim_counts(plens_root: Path) -> List[Tuple[str, int]]:
    out = []
    for scenario in sorted(plens_root.glob("*")):
        d = scenario / "delensed_sims"
        if not d.is_dir():
            continue
        n = len(list(d.glob("sim_*.fits")))
        out.append((scenario.name, n))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit delensing cache/runtime health")
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--runtime-root", type=Path, required=True)
    ap.add_argument(
        "--expected-cmb-size",
        type=int,
        default=0,
        help="Expected CMB raw file size in bytes. Use 0 to auto-detect modal size.",
    )
    ap.add_argument(
        "--expected-noise-size",
        type=int,
        default=0,
        help="Expected Noise raw file size in bytes. Use 0 to auto-detect modal size.",
    )
    args = ap.parse_args()

    repo_root = args.repo_root
    runtime_root = args.runtime_root

    pt_dir = repo_root / "THESIS" / "cache" / "pt_results"
    pp_dir = repo_root / "THESIS" / "cache" / "pp_results"
    plens_dir = runtime_root / "PLENS"
    cmb_raw = runtime_root / "CMB" / "sims" / "raw"
    noise_raw = runtime_root / "Noise" / "sims" / "raw"

    print("=== Cache Completeness ===")
    missing_pt = list_missing(pt_dir, EXPECTED_PT)
    missing_pp = list_missing(pp_dir, EXPECTED_PP)
    print(f"PT missing: {len(missing_pt)}")
    for name in missing_pt:
        print(f"  - {name}")
    print(f"PP missing: {len(missing_pp)}")
    for name in missing_pp:
        print(f"  - {name}")

    print("\n=== Raw File Size Checks ===")
    cmb_nominal, bad_cmb, cmb_hist = check_raw_sizes(
        cmb_raw, "dx12_v3_smica_cmb_mc_*_raw.fits", args.expected_cmb_size
    )
    noise_nominal, bad_noise, noise_hist = check_raw_sizes(
        noise_raw, "dx12_v3_smica_noise_mc_*_raw.fits", args.expected_noise_size
    )
    print(f"CMB nominal size used: {cmb_nominal}")
    print(f"CMB size classes: {len(cmb_hist)}")
    print(f"CMB abnormal-size files: {len(bad_cmb)}")
    for p in bad_cmb[:20]:
        print(f"  - {p.name} ({p.stat().st_size})")
    print(f"Noise nominal size used: {noise_nominal}")
    print(f"Noise size classes: {len(noise_hist)}")
    print(f"Noise abnormal-size files: {len(bad_noise)}")
    for p in bad_noise[:20]:
        print(f"  - {p.name} ({p.stat().st_size})")

    print("\n=== delensed_sims Population (by scenario) ===")
    for name, n in delensed_sim_counts(plens_dir):
        print(f"  - {name}: {n} sim_*.fits")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
