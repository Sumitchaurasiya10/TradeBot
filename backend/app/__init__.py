import os
import sys

# Ensure project root is in sys.path so imports like 'from backend.app...' work
# regardless of whether the user runs from project root or inside backend/
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_backend_dir)
for _p in (_root_dir, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)