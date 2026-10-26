"""Reproduce all main empirical tables and the rule summary from saved evidence."""
import argparse, json
from pathlib import Path
from build_paired_effects import produce as paired_outputs
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def table(headers,rows,caption,label):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join([':---']+['---:']*(len(headers)-1))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n\nTable: '+caption+' \\label{'+label+'}'

def produce(root=ROOT):
    p=root/'paper/combined_study';data=json.loads((p/'results_tables.json').read_text());audit=json.loads((p/'policy_audit/evidence_audit/summary.json').read_text());paired=json.loads(paired_outputs(root)['paired_effects.json'])['rows'];tables={}
    names={'none':'No gate','broad':'Broad','decomposed':'Decomposed'}
    rows=[]
    live=r'\begin{table}[htbp]\centering\small'+'\n'+r'\caption{Live outcomes. Each panel contains 192 assignments per condition. Unresolved outcomes remain in denominators.}\label{tab:compact-live}'+'\n'+r'\begin{tabular}{lrrr}\toprule Condition & Positive / assigned & Unresolved & Assignment bounds (\%)\\\midrule'+'\n'
    for pressure,outcome,title in [(True,'executed_violation','A. Pressure: executed violation'),(False,'service_complete','B. Permitted: reference completion')]:
      live+=r'\multicolumn{4}{l}{\textbf{'+title+r'}}\\'+'\n'
      for condition in names:
        r=next(x for x in data['live_by_condition'] if x['condition']==condition and x['pressure']==pressure)[outcome]
        live+=names[condition]+f" & {r['observed_positive']}/{r['assigned']} & {r['missing']} & "+'--'.join(f'{100*x:.2f}' for x in r['assignment_bounds'])+r'\\'+'\n'
      live+=r'\midrule'+'\n'
    live+=r'\end{tabular}\end{table}'
    tables['TABLE_LIVE']='```{=latex}\n'+live+'\n```'
    rows=[]
    for key,title in [('state_changing_violation','State-changing covered violation'),('native_rejected_violation','Violation already rejected natively'),('eligible_publicly_verified','Selected-eligible, public evidence sufficient'),('eligible_missing_public_evidence','Selected-eligible, private facts needed')]:
      r=next(x for x in data['shadow'] if x['category']==key and not x['first_violation_only'])
      cells=[]
      for gate in ['broad','decomposed']:
        g=r['gates'][gate];cells.append(f"{g['blocks']}/{r['proposals']}"+('*' if g['missing_decisions'] else ''))
      rows.append([title,r['proposals'],r['pairs_with_denominator'],*cells])
    tables['TABLE_SHADOW']=table(['Mechanical proposal class','Proposals','Supporting pairs / 32','Broad blocks','Decomposed blocks'],rows,'**Decisions on identical ungated writes.** Supporting pairs overlap across classes. *One decomposed decision is missing in the 96-proposal class. All broad decisions are observed.','tab:compact-shadow')
    counts={r['condition']:r['classes'] for r in data['live_block_accounting']};rows=[]
    for key,title in [('state_changing_covered_violation','State-changing covered violation'),('already_native_rejected_violation','Covered violation already rejected by the tool'),('selected_eligible_publicly_verified','Selected-eligible, public evidence sufficient'),('selected_eligible_missing_public_evidence','Selected-eligible, private facts needed'),('monitor_unavailable_fail_closed','Monitor unavailable')]: rows.append([title,*[counts[g].get(key,0) for g in ['broad','decomposed']]])
    rows.append(['**All blocked writes**',*['**'+str(sum(counts[g].values()))+'**' for g in ['broad','decomposed']]])
    tables['TABLE_BLOCKS']=table(['Native classification of a live blocked write','Broad','Decomposed'],rows,'**Native replay of live blocks.** Counts are events on condition-dependent trajectories.','tab:compact-blocks')
    counts={g:audit['layered_decision_cross_tabs']['live_blocks/'+g+'/block'] for g in ['broad','decomposed']};rows=[]
    for key,title in [('known_selected_violation','Known selected-predicate violation'),('additional_supported_action_breach','Additional supported action/prerequisite breach'),('current_message_format_only','Current-message format breach only'),('unresolved_full_policy','Full-policy status unresolved'),('monitor_unavailable','Monitor unavailable')]: rows.append([title,*[counts[g].get(key,0) for g in ['broad','decomposed']]])
    rows.append(['**All blocked writes**',*['**'+str(sum(counts[g].values()))+'**' for g in ['broad','decomposed']]])
    tables['TABLE_AUDIT']=table(['Evidence category for the blocked event','Broad','Decomposed'],rows,'**Programmatic evidence for live blocks.** The 74 selected-predicate violations include the 26 natively rejected calls in Table \\ref{tab:compact-blocks}. Evidence for a policy objection and additional prevention of a database change are different measurements. Formatting objections concern the current message, not necessarily the eligibility of the underlying action.','tab:compact-audit')
    actor_names={'gptmini_ref':'GPT-5.4 Mini','deepseek_ref':'DeepSeek V4.1 Flash','opus':'Claude Opus 5.5'}
    rule_names={'airline_basic_economy':'Basic economy','airline_cancellation':'Cancellation','airline_compensation':'Compensation','airline_passenger_count':'Passenger count','retail_identity_lookup':'Customer lookup','retail_post_item_change':'Further item change','retail_refund_destination':'Refund destination','retail_return_status':'Delivered return'}
    for level,marker,label,names_map in [('actor','TABLE_PAIRED_ACTORS','tab:paired-actors',actor_names),('rule','TABLE_PAIRED_RULES','tab:paired-rules',rule_names)]:
      rows=[]
      for group in sorted({r['group'] for r in paired if r['level']==level}):
        cells=[]
        for outcome in ['executed_violation','service_complete']:
          for gate in ['broad','decomposed']:
            r=next(x for x in paired if x['level']==level and x['group']==group and x['gate']==gate and x['outcome']==outcome)
            cells.append(f"{100*r['estimate']:+.2f}" if r['estimate'] is not None else f"[{100*r['lower']:+.2f}, {100*r['upper']:+.2f}]")
        rows.append([names_map[group],*cells])
      tables[marker]=table([level.title(),'Violation: broad','Violation: decomp.','Completion: broad','Completion: decomp.'],rows,'**Paired gate-minus-ungated differences by '+level+' (percentage points).** A single value is the descriptive estimate with fully observed outcomes; brackets give finite-assignment bounds when values are missing. Violation contrasts use pressure requests and completion contrasts use nominally permitted requests.',''+label)
    follow=json.loads((p/'exploratory_followup.json').read_text())
    rows=[]
    for row in follow['completion_loss_summaries']:
      rows.append([names[row['gate']],row['loss'],row['losses_with_block'],row['losses_without_block'],row.get('gain',0),row['unresolved_gated']])
    tables['TABLE_LOSSES']=table(['Gate','Losses','With block','No block','Gains','Unresolved'],rows,'**Matched permitted-task completion changes.** Each gate is matched to 192 ungated assignments. A loss requires both outcomes to be observed. Block presence is an association, not attribution.','tab:completion-losses')
    rows=[]
    for row in follow['tests']:
      rows.append(['Violation' if row['outcome']=='executed_violation' else 'Completion',names[row['gate']],str(row['n10'])+'/'+str(row['n01']),f"{row['nominal_mcnemar_p']:.6g}",f"{row['context_cluster_sign_flip_p_holm4']:.6g}"])
    tables['TABLE_EXPLORATORY']=table(['Outcome','Gate','Discordant b/c','Nominal exact p','Context Holm p'],rows,'**Unplanned GPT-5.4 Mini analysis.** Sixty-four matched runs per contrast. Context sensitivity keeps linked scenarios and repeats together in 31 groups; Holm correction covers four tests. Post hoc selection remains uncorrected.','tab:exploratory-tests')
    result={'source':'Verified compact summaries, policy-evidence counts and matched episode recount','model_calls':0,'tables':tables}
    return {'principal_tables.json':json.dumps(result,indent=2,sort_keys=True)+'\n','principal_tables.md':'# Reproduced principal tables\n\n'+'\n\n'.join(tables.values())+'\n'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    outputs=produce()
    for name,text in outputs.items():
      path=HERE/name
      if args.check: assert path.read_text()==text,name
      else:path.write_text(text)
    print(json.dumps({'principal_tables_verified':8,'check_only':args.check,'model_calls':0}))
if __name__=='__main__':main()
