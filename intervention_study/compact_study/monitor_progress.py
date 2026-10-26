"""Incremental offline integrity checks while the frozen collector runs."""
from collections import Counter
from datetime import datetime,timezone
import json,os,time
from pathlib import Path
from intervention_study.common import ROOT,read,save,digest
from intervention_study.compact_study.runner import BASE,verify,validate_record
from intervention_study.primary_study.native import replay
from intervention_study.primary_study.customer_audit import audit
from intervention_study.primary_study.evidence import Receipts


def stop_for_integrity(error_type,episode=None):
    incident={'utc':datetime.now(timezone.utc).isoformat(),'error_type':error_type,'episode':episode,
        'scope':'Recording or native replay integrity failure; no efficacy-based stop.'}
    save(BASE/'integrity_failure.json',incident)
    try:
        fd=os.open(BASE/'stop.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        return
    with os.fdopen(fd,'w') as stream:
        stream.write(json.dumps(incident,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())


def inspect(checked,cases,cells,receipts):
    verify()
    records=[read(p) for p in sorted((BASE/'episodes').glob('*.json'))]
    newly=0
    for rec in records:
        ep=rec['episode']
        if ep not in cells or any(rec.get(k)!=v for k,v in cells[ep].items()):raise ValueError('Allocation metadata mismatch')
        validate_record(rec, BASE, cells)
        if rec['status']=='started':continue
        source=digest(rec)
        if ep in checked:
            if checked[ep]['source_sha256']!=source:raise ValueError('Previously verified terminal record changed')
            continue
        native=replay(cases[rec['case_id']],rec,receipts)
        customer=audit(cases[rec['case_id']],rec,receipts)
        checked[ep]={'source_sha256':source,'native_replay_sha256':digest(native),
            'action_count':len(rec['actions']),'monitor_receipts_checked':True,'customer_audit':customer}
        newly+=1
        save(BASE/'incremental_integrity.json',{'checked':checked,
            'scope':'Operational replay and public-input integrity; no primary effect estimates or semantic-label validation. Customer flags remain descriptive and never trigger automatic exclusion.'})
    state=read(BASE/'pipeline_status.json') if (BASE/'pipeline_status.json').exists() else {}
    progress={'utc':datetime.now(timezone.utc).isoformat(),'assigned':len(cells),'recorded':len(records),
        'statuses':dict(Counter(r['status'] for r in records)),'native_verified_terminal_records':len(checked),
        'customer_flagged_records':sum(r['customer_audit']['flagged'] for r in checked.values()),
        'retained_stop':(BASE/'stop.json').exists(),'pipeline_phase':state.get('phase'),
        'scope':'Collection and integrity status only. No task/model selection or efficacy stopping.'}
    save(BASE/'progress.json',progress)
    if newly:print(json.dumps(progress),flush=True)
    return state.get('phase') in ['collection_and_analysis_complete','partial_collection_archived','pipeline_error']


def main():
    cases={c['case_id']:c for c in read(ROOT/'intervention_study/cases.json')}
    cells={c['episode']:c for c in read(BASE/'allocation.json')}
    path=BASE/'incremental_integrity.json';checked=read(path)['checked'] if path.exists() else {}
    receipts=Receipts(BASE)
    while True:
        try:finished=inspect(checked,cases,cells,receipts)
        except Exception as exc:
            stop_for_integrity(type(exc).__name__)
            raise
        if finished:break
        time.sleep(30)


if __name__=='__main__':main()
