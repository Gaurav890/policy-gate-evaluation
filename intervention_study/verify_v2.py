"""Verify original frozen inputs and a transparent development amendment."""
from intervention_study.common import BASE, ROOT, digest, read, verify_freeze

def verify_v2():
    verify_freeze()
    for rel,expected in read(BASE/'freeze_v2.json')['files'].items():
        assert digest(ROOT/rel)==expected,'Amended frozen source changed: '+rel
    return read(BASE/'protocol_v2.json')
