"""Preserve both earlier protocols and verify the fixed-customer amendment."""
from intervention_study.common import BASE,ROOT,digest,read
from intervention_study.verify_v2 import verify_v2

def verify_v3():
    verify_v2()
    for name,expected in read(BASE/'freeze_v3.json')['files'].items():assert digest(ROOT/name)==expected,name
    return read(BASE/'protocol_v3.json')
