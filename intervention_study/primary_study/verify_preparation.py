"""Offline preparation audit against retained development receipts and native tools."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import ROOT, read, save, digest
from intervention_study.primary_study.native import replay, summarize
from intervention_study.primary_study.customer_audit import audit
from intervention_study.primary_study.statistics import dependency_components
from intervention_study.scaled_design import pilot_report
from intervention_study.live_gating.records import archive
from intervention_study.verify_breadth import verify_breadth

BASE = Path(__file__).resolve().parent


def main():
    ledger=ROOT/'groundwork/spend_ledger.jsonl';before=digest(ledger) if ledger.exists() else None
    verify_breadth()
    old=ROOT/'intervention_study/scaled_design'
    for relative in ['pilot_freeze.json','repair_validation/freeze.json','repair_validation_v2/freeze.json']:
        for name,sha in read(old/relative)['files'].items():
            assert digest(ROOT/name)==sha, name
    allocation=read(BASE/'allocation.json');pairs={c['pair_id'] for c in allocation}
    assert len(allocation)==4608 and len({c['episode'] for c in allocation})==4608
    assert len(pairs)==48 and all(2<=int(p.rsplit('-',1)[1])<=7 for p in pairs)
    assert Counter(c['customer'] for c in allocation)=={'scripted':3456,'llm':1152}
    assert len({c['pair_id'] for c in allocation if c['customer']=='llm'})==16
    blocks=Counter((c['pair_id'],c['actor'],c['repeat'],c['customer']) for c in allocation)
    assert len(blocks)==576 and set(blocks.values())=={8}
    for key in blocks:
        assert {(c['pressure'],c['condition']) for c in allocation if (c['pair_id'],c['actor'],c['repeat'],c['customer'])==key}=={(p,g) for p in [False,True] for g in ['none','broad','decomposed','oracle']}
    cases={c['case_id']:c for c in read(ROOT/'intervention_study/cases.json')}
    reports=[];checks=[];all_receipts=0
    live=ROOT/'intervention_study/live_gating';receipts=archive();all_receipts+=len(receipts)
    for path in sorted((live/'episodes').glob('*.json')):
        rec=read(path);reports.append(replay(cases[rec['case_id']],rec,receipts))
    old_count=len(reports)
    for base in [old,old/'repair_validation',old/'repair_validation_v2']:
        with patch.object(pilot_report,'BASE',base):_,receipts=pilot_report.evidence()
        all_receipts+=len(receipts)
        for path in sorted((base/'episodes').glob('*.json')):
            rec=read(path);reports.append(replay(cases[rec['case_id']],rec,receipts))
            checks.append({'cohort':str(base.relative_to(ROOT)),**audit(cases[rec['case_id']],rec,receipts)})
    assert len(reports)==95 and old_count==64
    latest=[r for r in checks if r['cohort'].endswith('repair_validation_v2')]
    assert len(latest)==6 and not any(c['flagged'] for c in latest)
    older_blocks=[b for r in reports[:old_count] for b in r['blocks']]
    assert len(older_blocks)==25
    assert sum(b['direct_interception'] for b in older_blocks)==9
    assert sum(b['covered_violation'] and b['native_error'] and not b['native_state_change'] for b in older_blocks)==8
    assert (digest(ledger) if ledger.exists() else None)==before
    primary_attempts=len(list((BASE/'episodes').glob('*.json')))
    result={'historical_native_replays':len(reports),'historical_api_receipts_verified':all_receipts,
        'historical_blocks':25,'historical_direct_interceptions':9,'historical_native_rejected_violations':8,
        'primary_assigned':4608,'primary_attempts':primary_attempts,'primary_pairs':48,
        'connected_components':len(dependency_components(read(BASE/'dependencies.json'))),
        'development_freezes_verified':True,'allocation_balance_verified':True,'model_customer_latest_checks_passed':6,
        'customer_checks':checks,'ledger_sha256_before_and_after':before,'new_api_requests':0,
        'present_anonymous_artifact_hashes':{name:digest(ROOT/name) for name in ['output/pdf/expanded-review-draft.pdf','submission/supplement.zip','manuscript.pdf'] if (ROOT/name).exists()},
        'scope':'Engineering/native replay checks reuse the existing executable predicates; no independent semantic labels or primary effectiveness results.'}
    save(BASE/'preparation_verification.json',result)
    save(BASE/'historical_native_verification.json',{'records':reports,'summary':summarize(reports)})
    print('Verified 95 historical conversations, 25 blocked-write counterfactuals and all 4608 planned cells. No API calls.')


if __name__=='__main__':main()
