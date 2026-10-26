"""Freeze a held-out task-ID allocation and the analysis before collection."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json,MODELS
from prepare_manifest import build_manifest

if __name__=='__main__':
    benchmark=ROOT/'groundwork/benchmark-source'
    original=build_manifest(benchmark)
    assert original==json.loads((ROOT/'pilot_manifest.json').read_text())
    rows=[];ineligible=[]
    for domain in ['retail','airline']:
        tasks=json.loads((benchmark/'data/tau2/domains'/domain/'tasks.json').read_text())
        by_id={str(x['id']):x for x in tasks}
        candidates=original['domains'][domain]['reserved_upstream_test_ids']
        eligible=[]
        for tid in candidates:
            t=by_id[tid]
            if (t.get('initial_state') or {}).get('message_history'):
                ineligible.append({'domain':domain,'task_id':tid,'reason':'initial message history unsupported by external name mapping'})
            else:eligible.append(tid)
        ranked=sorted(eligible,key=lambda tid:hashlib.sha256(f'confirmatory-contract-audit-v1:{domain}:{tid}'.encode()).hexdigest())
        for tid in ranked[:6]:
            t=by_id[tid]
            signature=[x['name'] for x in (t.get('evaluation_criteria') or {}).get('actions') or []]
            family=domain+':'+hashlib.sha256(json.dumps(signature).encode()).hexdigest()[:12]
            rows.append({'domain':domain,'task_id':tid,'task_group':domain+':'+tid,'operation_sequence_family':family,
                         'reference_operation_sequence':signature})
    plan={'version':1,'scope':'Confirmatory descriptive audit on held-out task IDs; not a held-out task-family transfer or trained-detector comparison',
          'selection_seed':'confirmatory-contract-audit-v1','selection':'Six eligible upstream-test task IDs per domain by fixed SHA256 order; no outcome-based selection',
          'tasks':rows,'ineligible':ineligible,'actors':['claude','deepseek'],'conditions':['baseline','rename'],
          'episodes':len(rows)*4,'repeat':0,'sampling_seed':None,'max_steps':60,'customer':'claude','models':MODELS,
          'rename':'service_ prefix on tool names except calculate; rewrite public references; preserve parameters, executor, and native grading',
          'primary_outcomes':['frequency of explicit one-call/text-call contract violations among DB-matching completed trajectories',
                              'agreement between first model-monitor alert and first exact contract violation'],
          'monitor':'Frozen Gemini broad-failure prompt and 0.5 threshold from development; every generated assistant decision',
          'baselines':['never alert','any observed tool error','three identical calls','explicit interaction contract'],
          'analysis':'Report raw numerators/denominators by domain, actor and interface; task-cluster bootstrap plus operation-sequence-family sensitivity; no selection by p-values',
          'missingness':'Keep incomplete cells; infrastructure errors separate; per-request bounded retries; no unrecorded trajectory replacement',
          'secondary':'First-decision and first-batch/no-batch-last prefix renaming with repeated original controls, if remaining budget permits; separate from primary cohort',
          'native_labels':'DB match and explicit contract are separate; full native rewards with nonempty language checks remain pending unless independently evaluated',
          'stop':'Do not exceed existing $30 study authorization; actor collection ceiling $22 in reconciled holds; monitor ceiling $28; incomplete matrix must be disclosed',
          'claim_limits':'Convenience benchmark and mutable hosted models; within-source task-ID separation does not establish task-family or domain generalization',
          'benchmark_revision':original['benchmark_revision'],'benchmark_source_sha256':original['source_sha256']}
    path=ROOT/'study/confirmatory_manifest.json'
    if path.exists() and json.loads(path.read_text())!=plan:raise SystemExit('Existing manifest differs; create a new version')
    write_json(path,plan)
    print(json.dumps({'episodes':plan['episodes'],'tasks':rows,'ineligible':ineligible},indent=2))
