import os

# Centralized environment variable definitions
# Modify these paths at one place as needed
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Default paths (override via existing environment variables if set)
#
# Keeping the defaults project-relative avoids silently pointing cluster runs to
# stale machine-specific paths.
PLENS = os.environ.get('PLENS', os.path.join(PROJECT_ROOT, 'THESIS', 'PLENS'))
INPUT = os.environ.get('INPUT', os.path.join(PROJECT_ROOT, 'THESIS', 'SIMS'))
PARAMS = os.environ.get('PARAMS', os.path.join(PROJECT_ROOT, 'input'))
KFIELD = os.environ.get('KFIELD', os.path.join(PROJECT_ROOT, 'THESIS', 'LENSING'))

# Set the environment variables for the project
os.environ['PLENS'] = PLENS
os.environ['INPUT'] = INPUT
os.environ['PARAMS'] = PARAMS
os.environ['KFIELD'] = KFIELD
