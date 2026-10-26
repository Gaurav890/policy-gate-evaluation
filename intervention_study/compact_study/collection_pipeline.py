"""Finish shadow scoring and offline archiving after the authorized live collector exits."""
import fcntl,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from intervention_study.common import ROOT,read,save
from intervention_study.compact_study.runner import BASE,verify,approved_ceiling

def mark(phase,**extra):
    save(BASE/'pipeline_status.json',{'utc':datetime.now(timezone.utc).isoformat(),'phase':phase,**extra})

def command(module,*arguments):
    return subprocess.run([sys.executable,'-u','-m',module,*arguments],cwd=ROOT,check=True)

def main():
    verify();approved_ceiling();mark('waiting_for_live_collection')
    with (BASE/'.collection.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        allocation=read(BASE/'allocation.json')
        records=[read(p) for p in (BASE/'episodes').glob('*.json')]
        all_attempted=len(records)==len(allocation) and {r['episode'] for r in records}=={c['episode'] for c in allocation}
        stopped=(BASE/'stop.json').exists() or any(r['status']=='started' for r in records)
    if all_attempted and not stopped:
        mark('shadow_collection');command('intervention_study.compact_study.runner','--live','--phase','shadow')
    else:
        mark('collection_stopped',attempted=len(records),assigned=len(allocation),retained_stop=stopped)
    mark('archiving');command('intervention_study.compact_study.evidence')
    mark('offline_analysis');command('intervention_study.compact_study.analyze','--offline','--native')
    analysis=read(BASE/'analysis.json')
    stopped=(BASE/'stop.json').exists()
    shadow=list((BASE/'shadow').glob('*.json'))
    ready=analysis['recorded']==len(allocation) and len(shadow)==sum(c['condition']=='none' for c in allocation) and not stopped and all(read(p)['status']=='complete' for p in shadow)
    mark('collection_and_analysis_complete' if ready else 'partial_collection_archived',attempted=analysis['recorded'],assigned=len(allocation),retained_stop=stopped,shadow_sources=len(shadow))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        mark('pipeline_error',error_type=type(exc).__name__)
        raise
