"""Generate extension report and manuscript insert from completed saved results."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json

def frac(r):
    return f"{r['alerts']}/{r['denominator']}"+ (f" to {r['alerts']+r['unknown']}/{r['denominator']}" if r['unknown'] else '')
def table(headers,rows,columns):
    return '\\begin{tabular}{'+columns+'}\n\\toprule\n'+' & '.join(headers)+r'\\'+'\n\\midrule\n'+'\n'.join(' & '.join(map(str,row))+r'\\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n'
def main():
    x=json.loads((ROOT/'extension/analysis.json').read_text());cost=json.loads((ROOT/'extension/spending.json').read_text());plan=json.loads((ROOT/'extension/plan.json').read_text())
    assert x['completed']==24 and all(not m['unattempted'] for r in x['rows'] for m in r['monitors'].values())
    ds=x['original_second_monitor'];assert all(not r['deepseek']['unattempted'] for r in ds['rows'])
    clean_tasks=len({r['task_group'] for r in x['rows'] if r['state_success'] and not r['contract_violation']})
    changes=sum(r['contract_disagreement'] for r in x['repeated_pairs']);statechanges=sum(r['state_disagreement'] for r in x['repeated_pairs'])
    timing=ds['timing'];scored={m:sum(r['monitors'][m]['scored'] for r in x['rows']) for m in plan['monitor_models']};missing={m:sum(len(r['monitors'][m]['missing']) for r in x['rows']) for m in plan['monitor_models']}
    text='\\subsection{Exploratory extension: clean controls, a second monitor, and repeats}\n\\label{sec:extension}\n'
    text+='After the original analysis, a separate locally frozen extension selected three additional upstream-test IDs per domain by a fixed hash, excluding all original held-out IDs. It used DeepSeek as actor and the same Sonnet customer, with native instructions or an added actor-only reminder to issue one call per message, and two unseeded runs per task/condition. This yields 24 new conversations on six new task IDs. The step limit was 90 in both extension conditions, versus 60 originally. No proposals were edited, serialized, rejected, or resampled to obtain compliance. A two-cell feasibility gate permitted expansion if either reminder trajectory was contract-clean; both feasibility cells remain in the allocation. This is exploratory evidence, not a new confirmatory test or a family-disjoint sample.\n\n'
    text+=f"All 24 cells completed and replayed exactly. There are {sum(r['state_success'] for r in x['rows'])} state successes and {x['clean_successes']} contract-clean state successes from {clean_tasks} task IDs. Clean successes occur under both native and reminder instructions. Across the 12 task/condition repeat pairs, state success differs in {statechanges} pairs and contract compliance differs in {changes}. These repetitions show why a single rollout should not be treated as a stable task property; they do not isolate a causal benefit of the reminder.\n\n"
    text+='\\begin{table}[t]\n\\centering\\small\n\\caption{Separate extension cohort. Each row has three task IDs and two unseeded repeats. Clean success is state success without the measured interaction violation.}\n\\label{tab:extension}\n'
    text+=table(['Domain','Instructions','$n$','State successes','Clean successes'],[[r['domain'].title(),r['condition'],r['n'],r['state_successes'],r['clean_successes']] for r in x['strata']],'llrrr')+'\\end{table}\n'
    text+=f"DeepSeek V4.1 Flash also evaluated all 514 original public prefixes with the same broad prompt, schema, 512-token cap and 0.5 threshold, using its configured reasoning effort of none. There are {ds['scored_prefixes']} valid scores and {ds['missing_prefixes']} missing output(s). Of {ds['matched_prefixes']} matched valid Gemini/DeepSeek prefix pairs, {ds['matched_alert_disagreements']} disagree at the threshold. Prefix pairs are descriptive comparisons, not independent samples. The fixed 0.5 threshold is uncalibrated for both models, so their score scales need not be comparable. In one matched batch proposal (retail task 70, DeepSeek renamed actor, event 6), DeepSeek explicitly describes the four-call violation but assigns risk 0.35, versus Gemini's 1.0. Alert disagreement therefore need not mean failure to recognize a constraint. An exploratory fixed-threshold grid is supplied without selecting a preferred threshold. Table~\\ref{{tab:expanded-timing}} shows that the original coincidence between warning and violation onset does not generalize to the second monitor configuration. An alert preceding the interaction violation may concern another property; it is not thereby a correct forecast of eventual task failure.\n\n"
    text+=f"Both monitors also score the new conversations. Gemini supplies {scored['gemini']} valid scores ({missing['gemini']} missing), and DeepSeek supplies {scored['deepseek']} ({missing['deepseek']} missing). Among the {x['clean_successes']} clean state successes, the proxy-relative episode alert rate is {frac(x['rates']['gemini'])} for Gemini and {frac(x['rates']['deepseek'])} for DeepSeek. These denominators now exist, unlike in the original cohort, but cover only {clean_tasks} task IDs and do not certify semantic policy compliance. The native and reminder conditions remain separately tabulated in the artifact. Missing-score uncertainty is reported as lower/upper alert-count bounds rather than imputed negatives.\n\n"
    for model in plan['monitor_models']:
        rr=x['rates'][model];ci=rr['lower_task_bootstrap'];upper=rr['upper_task_bootstrap']
        text+=f"For {model.title()}, the descriptive whole-task bootstrap envelope is [{100*ci['low']:.1f}\\%, {100*upper['high']:.1f}\\%], excluding {ci['undefined_replicates']} of 5,000 replicates with no clean-success denominator. "
    text+='These small-support intervals do not establish deployment calibration. DeepSeek shares a model family with half the original actors and all extension actors; this dependence is disclosed rather than treated as independent model validation.\n\n'
    text+='The autonomous conversations are not comprehensively labeled for semantic-policy compliance. Optional human-review material is separate from the reported evidence; the later constructed eligibility experiment uses explicit simulator facts and executable labels instead. No independently human-reviewed result is claimed.\n'
    (ROOT/'paper/generated/extension.tex').write_text(text)
    report=f'''# Extension findings

The original study is unchanged; its manuscript and package are archived in `submission/archive-v001/`.

- Completed **24/24 additional conversations** on **six new task IDs**, with two runs per task/instruction condition.
- **{x['clean_successes']} clean state successes**, from **{clean_tasks} task IDs**; {sum(r['state_success'] for r in x['rows'])} state successes overall. No trace editing, serialization, rejection or discarded retries.
- **{changes}/12** repeat pairs change contract compliance; **{statechanges}/12** change state success.
- Second monitor: **{ds['scored_prefixes']}/514** valid original-prefix scores; {ds['missing_prefixes']} missing. First-alert timing: {json.dumps(timing)}.
- Matched valid original prefixes: **{ds['matched_alert_disagreements']}/{ds['matched_prefixes']}** alert disagreements. Do not treat prefixes as independent tasks.
- Extension clean-success alert counts: Gemini **{frac(x['rates']['gemini'])}**; DeepSeek **{frac(x['rates']['deepseek'])}**. These remain proxy-relative, not full-policy error rates.
- **Human review optional:** the separate review packet is outside the reported evidence. No human labels are incorporated.
- New response-reported spend: **${cost['extension_reported_usd']:.4f}**; cumulative **${cost['total_reported_usd']:.4f}**. Conservative hold **${cost['conservative_hold_usd']:.4f}** under the existing $30 cap.

The second monitor materially qualifies the original timing finding. More tasks and repeats do not establish family-disjoint or deployment-wide generalization. Seven clean successes are a useful denominator, not a precise estimate of a broad false-alarm rate. The later controlled eligibility cases support a separately scoped substantive-rule analysis; natural conversations remain without comprehensive semantic labels.
'''
    (ROOT/'extension/report.md').write_text(report)
    files=['extension/analysis.json','extension/spending.json','extension/plan.json','extension/replay.json','extension/threshold_sensitivity.json','extension/disagreements.md','paper/generated/extension.tex']
    write_json(ROOT/'extension/evidence_ledger.json',{'files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'human_labels_used':False})
    print('Generated extension findings and manuscript insert.')
if __name__=='__main__':main()
