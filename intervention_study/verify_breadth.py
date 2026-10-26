"""Verify the fixed extension to all as-yet-uncovered development rules."""
from intervention_study.common import BASE,ROOT,read,digest
from intervention_study.verify_v3 import verify_v3

def verify_breadth():
    verify_v3()
    for name,expected in read(BASE/'freeze_breadth.json')['files'].items():assert digest(ROOT/name)==expected,name
    return read(BASE/'protocol_breadth.json')
