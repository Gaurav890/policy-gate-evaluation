"""Archive the amended allocation with the existing exact-receipt implementation."""
from pathlib import Path
from intervention_study.primary_study.evidence import pack
if __name__ == '__main__':
    pack(Path(__file__).resolve().parent)
