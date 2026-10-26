"""Create the one-time primary source freeze before collection and funding approval."""
import importlib.metadata
import platform
from pathlib import Path
from intervention_study.common import ROOT, read, save, digest
from intervention_study.verify_breadth import verify_breadth

BASE=Path(__file__).resolve().parent


def main():
    if (BASE/'freeze.json').exists(): raise RuntimeError('Primary source freeze already exists')
    assert not list((BASE/'episodes').glob('*.json')) and not list((BASE/'shadow').glob('*.json'))
    approval=read(BASE/'authorization.json')
    assert approval['approved'] is False and approval['protocol_sha256']==digest(BASE/'protocol.json')
    verify_breadth()
    old=ROOT/'intervention_study/scaled_design'
    manifests=[ROOT/'intervention_study'/name for name in ['freeze.json','freeze_v2.json','freeze_v3.json','freeze_breadth.json']]
    manifests += [old/name for name in ['pilot_freeze.json','repair_validation/freeze.json','repair_validation_v2/freeze.json']]
    files={}
    for manifest in manifests:
        for name,sha in read(manifest)['files'].items():
            assert digest(ROOT/name)==sha, name
            files[name]=sha
        files[str(manifest.relative_to(ROOT))]=digest(manifest)
    save(BASE/'runtime_versions.json',{'python':platform.python_version(),
        'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions() if d.metadata.get('Name'))),
        'scope':'Observed preparation runtime. Hosted model aliases are separately recorded and are not immutable snapshots.'})
    extras=list(BASE.glob('*.py'))+list(BASE.glob('*.md'))+[BASE/name for name in ['allocation.json','protocol.json','dependencies.json','dependency_summary.json','precision_scenarios.json','precision_percentile_diagnostic.json','runtime_versions.json']]
    extras += [ROOT/'intervention_study'/name for name in ['verify_v2.py','verify_v3.py','verify_breadth.py','runtime_guarded_v3.py']]
    for path in extras:files[str(path.relative_to(ROOT))]=digest(path)
    save(BASE/'freeze.json',{'date':'2026-10-12','phase':'Before any primary collection; separate funding approval required',
        'files':dict(sorted(files.items())),
        'mutable_exclusions':['authorization.json','episodes/','shadow/','evidence/','execution.json','stop.json','analysis.json','native_verification.json','preparation_verification.json','historical_native_verification.json'],
        'policy':'Preserve this source freeze; any necessary collection change needs a visible prospective amendment and separate affected-cohort reporting.'})
    print('Frozen',len(files),'files. Collection remains unapproved.')


if __name__=='__main__':main()
