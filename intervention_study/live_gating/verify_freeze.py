"""Check preserved simulator provenance and the new online comparison freeze."""
from intervention_study.common import BASE, ROOT, read, digest
from intervention_study.verify_breadth import verify_breadth

def verify():
    verify_breadth()
    for rel,expected in read(BASE/'live_gating/freeze.json')['files'].items():
        assert digest(ROOT/rel)==expected,rel
    cfg=read(BASE/'live_gating/protocol.json')
    assert cfg['cumulative_ceiling_usd']==100
    assert len(read(BASE/'live_gating/allocation.json'))==cfg['planned_conversations']==64
    return cfg
