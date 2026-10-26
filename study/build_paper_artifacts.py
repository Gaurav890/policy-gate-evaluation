"""Generate manuscript numbers, tables, figures and a claim ledger from saved results."""
import hashlib,json,os,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.tooling/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

def esc(s):
    return str(s).replace('_',r'\_').replace('&',r'\&').replace('%',r'\%')
def table(headers,rows,spec):
    return '\\begin{tabular}{'+spec+'}\n\\toprule\n'+' & '.join(headers)+r'\\'+'\n\\midrule\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n\\bottomrule\n\\end{tabular}\n'
def pct(x):return f'{100*x:.1f}'+r'\%'
def main():
    r=json.loads((ROOT/'study/analysis/results.json').read_text());a=json.loads((ROOT/'study/policy-ablation-v002/summary.json').read_text())
    assert r['completed']==r['planned']==r['episode_metrics_identified']==48
    assert a['selected']==12
    out=ROOT/'paper/generated';out.mkdir(parents=True,exist_ok=True);fig=ROOT/'paper/figures';fig.mkdir(exist_ok=True)
    def emit(name,s): (out/(name+'.tex')).write_text(s+'\n')
    emit('macros',f"\\newcommand{{\\NComplete}}{{{r['completed']}}}\n\\newcommand{{\\NDiscord}}{{{r['discordance']['numerator']}}}\n\\newcommand{{\\NStateSuccess}}{{{r['state_successes']}}}")
    rows=[]
    for x in r['strata']:
        rows.append([x['domain'].title(),'Sonnet' if x['actor']=='claude' else 'DeepSeek',x['condition'],x['completed'],x['state_successes'],x['contract_violations'],x['state_successes_with_contract_violation']])
    emit('cohort_table',table(['Domain','Actor','Interface','$n$','$G=1$','$V=1$','$G=1,V=1$'],rows,'lllrrrr'))
    methods={'never':'Never alert','tool_error':'Observed tool error','repeat':'Repeated identical call','contract':'Exact contract','llm':'Language-model monitor'}
    rates=r['apparent_false_alarm_rates'];rows=[]
    for method,title in methods.items():
        cells=[]
        for target in ['state_success','state_and_contract_success']:
            v=rates[target][method];cells.append(f"{v['numerator']}/{v['denominator']} ({pct(v['rate'])})" if v['denominator'] else 'Undefined (0 negatives)')
        rows.append([title,*cells])
    emit('rates_table',table(['Monitor','State success $G=1$','State success and $V=0$'],rows,'lll'))
    d=r['discordance'];ci=d['task_bootstrap'];fam=d['operation_family_bootstrap'];t=r['first_alert_timing'];clean=rates['state_and_contract_success']['llm']['denominator']
    text=(f"All {r['completed']} planned cells completed, with {r['scored_prefixes']} of {r['expected_prefixes']} generated assistant decisions scored. {r['missing_prefixes']} prefixes lack valid structured output at the fixed token cap; these are retained as missing. In every affected conversation an observed alert precedes the missing prefix, so the episode-level any-alert decision and first-alert time remain identified. "
        f"There are {r['task_ids']} task IDs and {r['operation_families']} distinct reference-operation-sequence groups. "
        f"The native database check with normal termination marks {r['state_successes']} conversations as state successes; {r['contract_violations']} conversations contain an explicit interaction-contract violation. "
        f"Both labels hold in {d['numerator']}/{d['denominator']} state successes ({pct(d['rate'])}; the domain-stratified task bootstrap interval is [{pct(ci['low'])}, {pct(ci['high'])}]. "
        f"The operation-sequence-group sensitivity interval is [{pct(fam['low'])}, {pct(fam['high'])}]. "
        f"Both intervals are degenerate because every sampled state success violates the contract; they do not establish a population violation probability of one. Neither calculation had an undefined denominator ({ci['undefined_replicates']} and {fam['undefined_replicates']} of 5,000 replicates, respectively). "
        "Table~\\ref{tab:cohort} and Figure~\\ref{fig:matrix} preserve the individual strata and task cells.\n\n")
    ll=rates['state_success']['llm'];co=rates['state_success']['contract']
    text+=(f"Against state success alone, the language-model monitor alerts on {ll['numerator']}/{ll['denominator']} negatives ({pct(ll['rate'])}); "
        f"the exact contract detector alerts on {co['numerator']}/{co['denominator']} ({pct(co['rate'])}). "
        f"Adding the measured contract leaves {clean} negative conversations. "
        "Table~\\ref{tab:rates} reports the resulting denominators explicitly. This comparison changes the reference target while keeping the recorded alerts fixed; it is not a performance gain from retraining.\n\n")
    text+=(f"First alerts occur before the first contract violation in {t.get('before_first_contract',0)} conversations, at it in {t.get('at_first_contract',0)}, and after it in {t.get('after_first_contract',0)}. "
        f"There are {t.get('no_alert',0)} violating conversations with no alert and {t.get('no_observed_contract_violation',0)} conversations without an observed contract violation. "
        "Figure~\\ref{fig:timing} uses message-event indices rather than wall-clock latency. Coincidence with the first offending proposal is evidence of boundary detection, not advance warning of an unobserved failure. "
        "The deterministic contract baseline detects exactly the measured property by construction; its inclusion diagnoses target alignment rather than establishing a general-purpose monitor.")
    emit('results_text',text)
    arms=a['arms'];control=a['repeat_control']
    emit('ablation_text',(f"Of the {a['selected']} preselected held-out cells, {a['eligible']} supply an eligible batch proposal and {a['ineligible']} are ineligible; no replacement is made. "
        f"The strict-repeat arm alerts on {arms['strict_repeat']['alerts']}/{a['eligible']} eligible prefixes. Relaxing only the batch rule yields {arms['relaxed_policy']['alerts']}/{a['eligible']} alerts, "
        f"and the outcome-focused prompt yields {arms['outcome_target']['alerts']}/{a['eligible']}. "
        f"The strict repeat changes {control['alert_flips']} alert decisions relative to the original monitor score at the same boundary (mean absolute risk difference {control['mean_absolute_risk_change']:.4f}). "
        "Table~\\ref{tab:ablation} reports matched risk changes. These descriptive interventions expose sensitivity to the stated policy and requested target. They do not establish that the outcome-focused scores are calibrated, that every residual alert is correct, or that relaxing the rule improves live agent behavior."))
    rows=[]
    for arm,title in [('strict_repeat','Strict repeat'),('relaxed_policy','Relaxed batch rule'),('outcome_target','Outcome-focused target')]:
        v=arms[arm];rows.append([title,f"{v['alerts']}/{v['n']}",f"{v['mean_risk']:.3f}",f"{v['mean_risk_change_from_strict']:+.3f}",v['alert_flips_from_strict']])
    emit('ablation_table',table(['Input arm','Alerts','Mean risk',r'$\Delta$ vs. strict','Alert flips'],rows,'lrrrr'))
    plan=json.loads((ROOT/'study/confirmatory_manifest.json').read_text())
    rows=[[x['domain'].title(),x['task_id'],r'\texttt{'+esc(x['operation_sequence_family'].split(':')[1])+'}',len(x['reference_operation_sequence'])] for x in plan['tasks']]
    emit('task_table','\\begin{center}\n'+table(['Domain','Test task ID','Operation-sequence group','Reference calls'],rows,'lllr')+'\\end{center}\nAll listed IDs come from the pinned upstream test split. An empty reference sequence is retained and may correspond to a legitimate no-mutation task; it does not establish semantic task success.')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    conditions=[('claude','baseline'),('claude','rename'),('deepseek','baseline'),('deepseek','rename')]
    data=[]
    for task in plan['tasks']:
        rr=[]
        for actor,condition in conditions:
            row=next(x for x in r['rows'] if x['task_group']==task['task_group'] and x['actor']==actor and x['condition']==condition)
            rr.append(int(row['state_success'])+2*int(row['contract_violation']))
        data.append(rr)
    colors=['#e5e7eb','#6baed6','#fdae6b','#a63603'];labels=['State fail; contract clean','State pass; contract clean','State fail; contract violation','State pass; contract violation']
    f,ax=plt.subplots(figsize=(7.2,5.1));ax.imshow(data,cmap=ListedColormap(colors),vmin=-.5,vmax=3.5,aspect='auto')
    ax.set_xticks(range(4),['Sonnet\noriginal','Sonnet\nrenamed','DeepSeek\noriginal','DeepSeek\nrenamed']);ax.set_yticks(range(12),[x['task_group'] for x in plan['tasks']]);ax.set_xlabel('Actor and interface')
    for i,row in enumerate(data):
        for j,v in enumerate(row):ax.text(j,i,['F / C','P / C','F / V','P / V'][v],ha='center',va='center',color='white' if v==3 else '#111827',fontsize=9)
    ax.axhline(5.5,color='white',linewidth=2);ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,labels)],bbox_to_anchor=(.5,-.15),loc='upper center',ncol=2,frameon=False,fontsize=8)
    f.subplots_adjust(left=.19,bottom=.25,right=.98,top=.99);f.savefig(fig/'label_matrix.pdf',metadata={'Creator':'Matplotlib','Author':'','CreationDate':None,'ModDate':None});plt.close(f)
    pairs=Counter((x['first_contract'],x['first_llm_alert']) for x in r['rows'] if x['first_contract'] is not None and x['first_llm_alert'] is not None)
    f,ax=plt.subplots(figsize=(5.4,4.2));limit=max([max(k) for k in pairs]+[1])+2
    ax.plot([0,limit],[0,limit],color='#6b7280',linestyle='--',linewidth=1,label='Same decision boundary')
    for (x,y),count in pairs.items():
        ax.scatter(x,y,s=100+35*count,color='#2166ac',edgecolor='white',linewidth=.8,zorder=3);ax.text(x,y,str(count),ha='center',va='center',fontsize=8,color='white',zorder=4)
    ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='First contract violation (event index)',ylabel='First monitor alert (event index)');ax.legend(frameon=False,fontsize=8,loc='lower right');f.tight_layout();f.savefig(fig/'alert_timing.pdf',metadata={'Creator':'Matplotlib','Author':'','CreationDate':None,'ModDate':None});plt.close(f)
    sources=['study/analysis/results.json','study/policy-ablation-v002/summary.json','groundwork/invariance-v002/summary.json','study/confirmatory_manifest.json','study/spending.json']
    ledger={'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'claims':{
      'abstract_completed':'results.completed','abstract_discordance':'results.discordance.numerator / denominator','cohort_table':'results.strata',
      'false_alarm_table':'results.apparent_false_alarm_rates','timing_figure':'results.rows[first_contract, first_llm_alert]',
      'intervals':'results.discordance.task_bootstrap and operation_family_bootstrap','ablation':'policy-ablation-v002/summary.json.arms',
      'development_renaming':'invariance-v002/summary.json','costs':'study/spending.json.reported_cost_usd and requests'},'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(ROOT/'study/analysis/claim_ledger.json',ledger)
    print('Generated verified manuscript tables, text, figures, and claim ledger.')
if __name__=='__main__':main()
