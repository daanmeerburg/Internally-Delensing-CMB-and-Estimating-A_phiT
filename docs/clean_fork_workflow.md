# Repository Maintenance

## Purpose

This repository should now be treated as the primary standalone analysis fork.
The goal is to keep it runnable without depending on an older dirty checkout or
manual knowledge that only existed in the original development environment.

## Working Rules

1. Keep generated products out of Git.
2. Keep pipeline code, notebook cache builders, and documentation in version control.
3. Run expensive production steps through Slurm, not interactive shells.
4. Treat the directories pointed to by `PLENS`, `INPUT`, `PARAMS`, and `KFIELD`
   as runtime state, not repository state.

## Recommended Git Workflow

For normal work in this fork:

```bash
git checkout -b <feature-branch>
# edit code or docs
# run the relevant Slurm job or notebook smoke test
git add <files>
git commit -m "<message>"
git push -u origin <feature-branch>
```

If you still want to track the historical upstream repository, keep it only as a
reference remote:

```bash
git remote add upstream https://github.com/gdijkman3-source/Internally-Delensing-CMB-and-Estimating-A_phiT.git
```

But the documentation in this fork should assume `origin` is the main working
repository.

## What Belongs In Git

Keep in Git:

- analysis code under the repository root
- `parfiles/`
- `docs/`
- notebook sources under `THESIS/`
- Slurm wrappers and cache-building scripts
- small configuration files such as `requirements.txt`

Do not keep in Git:

- `THESIS/cache/`
- generated figures such as `THESIS/*.png`
- `__pycache__/`
- rebuilt local binary artifacts unless you explicitly decide to version them
- large runtime outputs written under `PLENS`

## Reproducibility Notes

A fresh clone should be made runnable by:

1. creating a Python 3.10 environment
2. installing the requirements
3. configuring `PLENS`, `INPUT`, `PARAMS`, and `KFIELD`
4. building any required local binary extensions on the target cluster
5. running the Slurm wrappers that generate pipeline outputs and notebook caches
6. building local binary extensions such as `plancklens/wigners` on the target system

The docs in this repository should describe those steps directly, without
assuming access to an older checkout.
