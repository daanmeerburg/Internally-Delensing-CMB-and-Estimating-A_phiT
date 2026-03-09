# Clean Fork Workflow

## Recommendation

Do not continue cleanup or documentation work in the current checkout of
`Internally-Delensing-CMB-and-Estimating-A_phiT`. It contains an unresolved merge
conflict and local runtime artifacts.

Instead:

1. Fork the upstream repository to your own GitHub account.
2. Clone your fork into a fresh directory.
3. Add the original repository as `upstream`.
4. Re-apply only the changes you want to keep from the current dirty tree.
5. Do documentation and cleanup work in a dedicated branch.

## Suggested Repository Setup

```bash
cd /home3/p283342/Delensing

# After you create your fork on GitHub:
git clone git@github.com:<your-user>/Internally-Delensing-CMB-and-Estimating-A_phiT.git clean-delensing
cd clean-delensing

git remote add upstream https://github.com/gdijkman3-source/Internally-Delensing-CMB-and-Estimating-A_phiT.git
git fetch upstream
git checkout -b docs/pipeline-notes upstream/main
```

If you prefer HTTPS:

```bash
git clone https://github.com/<your-user>/Internally-Delensing-CMB-and-Estimating-A_phiT.git clean-delensing
```

## What To Carry Over From The Current Tree

Carry over carefully:

- Any intentional changes to `env_config.py`
- Any intentional changes to `run_parfiles.py`
- Any scientific changes inside `parfiles/Noise/*.py`
- Your runtime environment notes for `delens-env`
- The new downloader script if you want it versioned

Do not carry over blindly:

- `__pycache__/`
- compiled `.so` changes unless you know why they changed
- `Python-3.10.17/`
- `Python-3.10.17.tar.xz`
- generated output inside `THESIS/PLENS/`
- unresolved merge markers or conflict state

## First Cleanup Commit Sequence

Recommended commit order:

1. `docs: add pipeline overview and data layout`
2. `docs: explain parfile variants and estimators`
3. `refactor: remove hardcoded environment paths`
4. `refactor: wrap run_parfiles in a main entry point`
5. `chore: update gitignore for caches and generated outputs`

## Notes On `delens-env`

If `delens-env` is the environment that actually runs the project, treat it as
the current source of truth and record:

- Python version
- `pip freeze` or at least the manually installed extra packages
- how `PLENS`, `INPUT`, `PARAMS`, and `KFIELD` are exported

That information belongs in the clean fork README.
