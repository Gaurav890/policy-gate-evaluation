"""Generate final expansion tables and statements only from fully accounted outputs."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from replication.common import ROOT,BASE,write_json
NAMES={'gemini':'Gemini','deepseek':'DeepSeek','gptmini':'GPT-5.4 Mini'}
def frac(r):
 n=r['denominator'];lo=r['alerts'];hi=lo+r['unknown']
 return 'Undefined' if not n else f'{lo}/{n}' if hi==lo else f'{lo}--{hi}/{n}'
def table(headers,rows,fmt):return '\\begin{tabular}{'+fmt+'}\n\\toprule\n'+' & '.join(headers)+r'\\'+'\n\\midrule\n'+'\n'.join(' & '.join(str(x) for x in row)+r'\\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n'
def plot_targets(r):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(7.0,3.2))
 colors={'state':'#a44000','clean':'#1557a5'}
 for index,m in enumerate(NAMES):
  one=r['state_rates'][m];two=r['clean_rates'][m]
  if one['lower'] is not None and two['lower'] is not None:ax.plot([one['lower']*100,two['lower']*100],[index,index],color='#c4cbd4',linewidth=3,zorder=1)
  for key,z,dy,marker,label in [('state',one,.12,'s','State success'),('clean',two,-.12,'o','State success + interaction compliance')]:
   if z['lower'] is None:continue
   x=z['lower']*100;high=z['upper']*100;y=index+dy
   ax.plot([x,high],[y,y],color=colors[key],linewidth=4,zorder=2)
   ax.scatter([x],[y],s=48,color=colors[key],marker=marker,label=label if index==0 else None,zorder=3)
   ax.annotate(frac(z).replace('--','-'),(x,y),xytext=(0,9 if dy>0 else -16),textcoords='offset points',ha='center',fontsize=8)
 ax.set_yticks(range(len(NAMES)),list(NAMES.values()));ax.set_xlim(-5,108);ax.set_ylim(-.7,2.7);ax.set_xlabel('Episode alerts among the selected negative class (%)');ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.24),ncol=2,frameon=False,fontsize=8);fig.tight_layout()
 fig.savefig(ROOT/'paper/figures/expanded_targets.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
def main():
 x=json.loads((BASE/'analysis.json').read_text());r=x['replication'];cost=json.loads((BASE/'spending.json').read_text());p=json.loads((BASE/'plan.json').read_text())
 assert r['completed']+len(r['incomplete'])==168
 for cohort in ['original','extension','replication']:
  for row in x[cohort]['rows']:
   assert all(not m['0.5']['unattempted'] for m in row['monitors'].values())
 assert all(not target['unattempted'] for model in x['controlled_policy'].values() for target in model.values())
 s='\\subsection{Complete remaining-test expansion and independent-family monitor}\n\\label{sec:replication}\n'
 s+='A subsequent protocol, frozen before these new outcomes but after the earlier findings, allocates every remaining reserved upstream-test ID: 31 retail and 11 airline tasks. Each uses the same DeepSeek actor and Sonnet customer, native or reminder instructions, and two unseeded repeats, for 168 planned conversations. The 90-step and 900-second limits match the first extension. All attempted cells are retained, with interruptions separate from completed trajectories; no failed cell is invisibly replaced. This is an explicitly exploratory expansion of the original study, not a retrospectively declared confirmatory sample. Together the allocations cover all 60 reserved test IDs, but do not establish 60 independent task families.\n\n'
 s+=f"Of the 168 attempts, {r['completed']} completed and {len(r['incomplete'])} were interrupted. Completed runs include {r['state_successes']} state successes and {r['clean_successes']} contract-clean state successes across {r['clean_task_ids']} task IDs. Table~\\ref{{tab:replication-cohort}} preserves domain and instruction strata. Rates below condition on completed runs; infrastructure missingness need not be random, and interrupted attempts remain in the released inventory.\n\n"
 s+='\\begin{table}[t]\\centering\\small\n\\caption{Remaining-test expansion. Completed conversations, state successes, and contract-clean state successes; clean IDs count distinct tasks contributing a clean success.}\\label{tab:replication-cohort}\n'
 s+=table(['Domain','Instruction','Completed','$G=1$','$G=1,V=0$','Clean IDs'],[[z['domain'].title(),z['condition'],z['n'],z['state_successes'],z['clean_successes'],z['clean_tasks']] for z in r['strata']],'llrrrr')+'\\end{table}\n'
 s+=f"The exact interaction-rule baseline alerts on {r['state_successes']-r['clean_successes']}/{r['state_successes']} state successes and 0/{r['clean_successes']} interaction-clean state successes, by construction. This directly instantiates Equation~\\ref{{eq:decomposition}} with a nonempty clean negative class; it is a transparent diagnostic, not a learned detection result.\n\n"
 s+='GPT-5.4 Mini, served through a fixed provider route with reasoning effort none, is a third monitor from a family absent from the actors and customer simulator. It scores all original and first-extension prefixes; all three monitors score every generated assistant prefix of each completed new conversation. The broad prompt, response schema and 512-token cap are unchanged. We retain the original fixed 0.5 threshold and provide the same fixed sensitivity grid, without selecting a threshold from these results. Independence of model family does not establish independence of training data.\n\n'
 s+='\\begin{table}[t]\\centering\\small\n\\caption{Alerts among contract-clean state successes, separately by collection cohort. A range reflects unidentified episode alerts due to missing scores, not a confidence interval. All rates remain relative to the measured state/interaction target.}\\label{tab:expanded-monitors}\n'
 s+=table(['Monitor','First extension','Remaining-test expansion'],[[NAMES[m],frac(x['extension']['clean_rates'][m]),frac(r['clean_rates'][m])] for m in NAMES],'lll')+'\\end{table}\n'
 comparisons=[]
 for m in NAMES:
  a=r['state_rates'][m];b=r['clean_rates'][m];comparisons.append(f"{NAMES[m]} changes from {frac(a)} ({100*a['lower']:.1f}\\%) to {frac(b)} ({100*b['lower']:.1f}\\%)")
 s+='Changing the negative class has a configuration-dependent direction: '+ '; '.join(comparisons)+'. DeepSeek increases under the additional interaction-compliance condition, whereas the other two decrease. Equation~\\ref{eq:decomposition} permits either direction because the monitor need not behave like the exact rule baseline. The evaluation target must be declared on substantive grounds, without selecting whichever definition yields the preferred rate.\n\n'
 for m in NAMES:
  z=r['clean_rates'][m];lo=z['bootstrap_lower'];hi=z['bootstrap_upper']
  if lo['low'] is not None:s+=f"For {NAMES[m]}, the descriptive whole-task bootstrap envelope on new clean successes is [{100*lo['low']:.1f}\\%, {100*hi['high']:.1f}\\%], with {lo['undefined_replicates']} of 5,000 resamples lacking a denominator. "
 s+='These intervals describe resampling of finite benchmark tasks; they do not certify population coverage or deployment calibration. Full domain/condition strata and missing-score bounds are included in the artifact.\n\n'
 s+='\\begin{figure}[t]\\centering\n\\includegraphics[width=.90\\linewidth]{figures/expanded_targets.pdf}\n\\caption{The same broad-monitor decisions evaluated against two negative classes in the remaining-test expansion. Labels give alert counts and denominators. Gray lines connect the two target-specific rates; colored horizontal spans, where present, show missing-score bounds rather than confidence intervals.}\\label{fig:expanded-targets}\n\\end{figure}\n'
 q=r['repeated_pairs'];s+=f"Among {q['complete_pairs']} task/condition pairs with both repeats completed, {q['contract_discordance']} change interaction-contract status and {q['state_discordance']} change state-success status. These comparisons expose run variability and do not isolate a causal benefit of adding the reminder.\n\n"
 s+='\\begin{table}[t]\\centering\\small\n\\caption{First-alert timing relative to the first measured interaction violation. Contract-clean conversations are outside this timing denominator.}\\label{tab:expanded-timing}\n'
 s+=table(['Cohort','Monitor','Before','At','After','No alert','Unidentified'],[[('Original' if cohort=='original' else 'Expansion'),NAMES[m],*[x[cohort]['timing'][m][k] for k in ['before','at','after','no_alert','unidentified']]] for cohort in ['original','replication'] for m in NAMES],'llrrrrr')+'\\end{table}\n'
 s+='\\subsection{Constructed substantive-policy contrasts without human labels}\n\\label{sec:policy-lab}\n'
 s+='To test a substantive rule separately from harmless tool batching, we construct 24 matched cancellation pairs: six rule contrasts across four deterministically selected source reservations, with an eligible and an ineligible variant in each pair. The contrasts cover booking age, airline cancellation, business cabin, health insurance, covered weather reason, and a previously flown segment. All prefixes supply the user and reservation IDs, cancellation reason, native reservation and flight-status observations, and explicit confirmation. Each ends with the same single, text-free cancellation proposal within its pair. Labels concern only cancellation eligibility, not comprehensive policy compliance.\n\n'
 s+='Eligibility is computed from explicit simulator facts using two separately written formulations of the stated rule, checked over a factorial grid. This is implementation cross-checking, not independent human adjudication. Boundary-ambiguous exact 24-hour bookings are excluded from the fixtures. All 48 proposed cancellations execute through the native tool, including the 24 ineligible ones; all 48 satisfy the measured interaction contract. This demonstrates a gap between operation execution, interaction formatting, and substantive eligibility within the constructed cases. The operation-executed label is not the native task-success label $G$, and these synthetic probes are not additional autonomous actor conversations.\n\n'
 s+='Each monitor sees the identical public input twice, under the original broad target and a cancellation-eligibility-only target, in alternating order. Ground-truth labels, fixture identifiers, final database state and post-action results are excluded from monitor inputs.\n'
 s+='\\begin{table}[t]\\centering\\small\n\\caption{Constructed policy cases: alerts at threshold 0.5 among 24 eligible and 24 ineligible cancellations. The focused target concerns cancellation eligibility only. Missing scores produce count ranges. These are controlled-case counts, not natural violation prevalence or deployment error estimates.}\\label{tab:policy-lab}\n'
 rows=[]
 for m in NAMES:
  for t in ['broad','eligibility']:
   z=x['controlled_policy'][m][t]['thresholds']['0.5'];rows.append([NAMES[m],t,frac(z['eligible']),frac(z['ineligible'])])
 s+=table(['Monitor','Target','Eligible alerts','Ineligible alerts'],rows,'llll')+'\\end{table}\n'
 s+='The artifact reports score-direction changes within every pair and all six rule strata, including failures. Four reused source reservations and six constructed rule contrasts do not form a representative semantic-policy benchmark. No human-labeled accuracy, naturally occurring semantic-violation rate, calibrated risk probability or repair benefit is claimed.\n'
 coverage=[]
 for cohort in ['original','extension','replication']:
  for model in NAMES:
   ms=[row['monitors'][model]['0.5'] for row in x[cohort]['rows']]
   coverage.append([cohort.title(),NAMES[model],sum(z['scored'] for z in ms),sum(z['missing'] for z in ms),sum(not z['any_identified'] for z in ms),sum(not z['first_identified'] for z in ms)])
 appendix='\\section{Monitor coverage and executable eligibility}\n'
 appendix+='\\begin{table}[h]\\centering\\small\n\\caption{All requested decision prefixes. Missing outputs are retained. Unidentified episode labels count conversations whose any-alert status or first-alert timing cannot be determined from the available scores.}\\label{tab:coverage}\n'
 appendix+=table(['Cohort','Monitor','Valid','Missing','Unknown any','Unknown first'],coverage,'llrrrr')+'\\end{table}\n'
 appendix+='For the constructed fixtures, let $a$ be booking age in hours, $F$ indicate any flying or landed segment, $C$ indicate that all segments are cancelled by the airline, $B$ indicate business cabin, $I$ indicate purchased insurance, and $R$ indicate a health or weather reason. The executable eligibility label is\n\\[ E=\\neg F\\;\\land\\;\\bigl[(0\\leq a<24)\\lor C\\lor B\\lor(I\\land R)\\bigr]. \\]\n'
 appendix+='Fixtures use the policy clock (15 May 2024, 15:00 EST), exclude exact 24-hour bookings, and contain nonempty itineraries with uniform segment status. Mixed-status itineraries are untested. Both implementations agree over 432 factorial fact combinations; this is implementation cross-checking, not independent policy adjudication.\n'
 (ROOT/'paper/generated/monitor_coverage.tex').write_text(appendix)
 plot_targets(r)
 (ROOT/'paper/generated/replication.tex').write_text(s)
 report=f'''# Final simulation expansion

- Fixed allocation: 168 new attempts on all 42 previously unused reserved test IDs.
- Completed: {r['completed']}; interrupted and retained: {len(r['incomplete'])}.
- New state successes: {r['state_successes']}; interaction-clean state successes: {r['clean_successes']} across {r['clean_task_ids']} task IDs.
- Three monitors: Gemini, DeepSeek, and GPT-5.4 Mini. Every completed trajectory's decision prefixes are accounted for; missing outputs are not negatives.
- Constructed substantive-policy test: 48 native simulator cases, 24 matched pairs, six rule contrasts, four source reservations. Both eligibility classes execute cancellation; this is not natural prevalence evidence.
- No human labels are used or required for the declared mechanical targets. The optional review website is separate.
- Total reported API cost: ${cost['cumulative_reported_usd']:.6f}; new expansion cost: ${cost['new_reported_usd']:.6f}; conservative admission hold: ${cost['conservative_hold_usd']:.6f}; authorization: ${cost['authorized_cap_usd']:.2f}.

This is a reproducible, limited evaluation audit. More simulations improve coverage of this benchmark, not guarantees of acceptance or deployment safety.
'''
 report+='\n## What the results mean\n\nReaching the expected database state and following a stated rule are different checks. The monitor can warn about a rule breach even when the final state matches. Changing which successful conversations count as negatives therefore changes the measured alert rate. These are rates relative to explicit proxy targets, not independently verified errors against every policy requirement.\n\n'
 report+='| Monitor | Alerts among new state successes | Alerts among new interaction-clean state successes |\n|---|---:|---:|\n'
 for m in NAMES:report+=f"| {NAMES[m]} | {frac(r['state_rates'][m])} | {frac(r['clean_rates'][m])} |\n"
 report+='\nThe change is not uniformly downward: DeepSeek has a higher alert rate in the interaction-clean subset, while Gemini and GPT-5.4 Mini have lower rates. These monitors do not behave like the exact interaction-rule baseline.\n'
 report+='\nA count range means missing scores prevent an exact episode label. It is not a confidence interval. The exact rule baseline gives '+str(r['state_successes']-r['clean_successes'])+'/'+str(r['state_successes'])+' and 0/'+str(r['clean_successes'])+' respectively, by construction.\n\n'
 report+='| Monitor | Cancellation target | Eligible alerts (24 cases) | Ineligible alerts (24 cases) |\n|---|---|---:|---:|\n'
 for m in NAMES:
  for target in ['broad','eligibility']:
   z=x['controlled_policy'][m][target]['thresholds']['0.5'];report+=f"| {NAMES[m]} | {target} | {frac(z['eligible'])} | {frac(z['ineligible'])} |\n"
 report+='\nThe controlled cases show why successful tool execution cannot certify cancellation eligibility. They are designed examples with four reused source reservations, not evidence about how often real agents violate policies. Configuration differences, including reasoning settings, limit model-ranking interpretations. Human review is optional for these mechanical labels; it would be needed to support additional ambiguous judgments presented as human-validated evidence.\n\n'
 report+='## Remaining author actions\n\nReview the manuscript and its limitations, finalize authorship and private submission metadata, and authorize actual submission. No paper has been submitted. Completing experiments and formatting does not guarantee acceptance.\n'
 (BASE/'report.md').write_text(report)
 files=['replication/analysis.json','replication/plan.json','replication/spending.json','replication/replay.json','replication/policy_lab/cases.json','paper/generated/replication.tex','paper/figures/expanded_targets.pdf','paper/generated/monitor_coverage.tex','replication/failure_audit.json']
 write_json(BASE/'evidence_ledger.json',{'files':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'human_labels_used':False})
 print('Generated final simulation report and manuscript tables.')
if __name__=='__main__':main()
