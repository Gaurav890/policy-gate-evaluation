"""Recompute earlier main-text evidence from saved episodes and scores, without writes or calls."""
import contextlib,io,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from replication import analyze as replication
from substantive_evaluation import analyze as substantive

def verify():
    rebuilt={}
    def capture(path,value):
        saved=json.loads(Path(path).read_text())
        assert saved==value,'Recomputed historical analysis differs: '+str(Path(path).relative_to(ROOT))
        rebuilt[str(Path(path).relative_to(ROOT))]=value
    old=replication.write_json;argv=sys.argv
    try:
        replication.write_json=capture;sys.argv=['verify_supporting_results','--final']
        with contextlib.redirect_stdout(io.StringIO()):replication.main()
    finally:replication.write_json=old;sys.argv=argv
    old=substantive.dump
    try:
        substantive.dump=lambda name,value:capture(ROOT/'substantive_evaluation'/name,value)
        with contextlib.redirect_stdout(io.StringIO()):substantive.main()
    finally:substantive.dump=old
    r=rebuilt['replication/analysis.json'];s=rebuilt['substantive_evaluation/analysis.json'];editor=(ROOT/'paper/editorial/replication.tex').read_text();ext=(ROOT/'paper/editorial/substantive_extension.tex').read_text()
    names={'gemini':'Gemini','deepseek':'DeepSeek','gptmini':'GPT-5.4 Mini'}
    rows=[]
    for cohort,title in [('original','Original'),('replication','Expansion')]:
      for model,label in names.items():
        z=r[cohort]['timing'][model]
        values=[z.get(k,0) for k in ['before','at','after','no_alert','unidentified']]
        row=' & '.join(map(str,[title,label,*values]))+r'\\'
        assert row in editor,row
        rows.append(row)
    timing='\n'.join(rows)+'\n';rows=[]
    for model,label in names.items():
      for target in ['broad','eligibility']:
        z=r['controlled_policy'][model][target]['thresholds']['0.5']
        values=[str(z[k]['alerts'])+'/'+str(z[k]['denominator']) for k in ['eligible','ineligible']]
        row=' & '.join([label,target,*values])+r'\\';assert row in editor,row;rows.append(row)
    cancellation='\n'.join(rows)+'\n';rows=[]
    for model,label in [('gemini','Gemini 3.8 Flash'),('gptmini','GPT-5.4 Mini')]:
      z=next(x for x in s['comparisons'] if x['cohort']=='substantive_evaluation/episodes' and x['model']==model and x['threshold']==.5 and x['difference']=='broad minus substantive' and x['subset']=='interaction_clean_no_policy_tool_discrepancy')
      value=f"{100*z['mean']:+.1f}";value='$'+value+'$' if value.startswith('-') else value
      row=' & '.join(map(str,[label,z['matched_prefixes'],z['n_tasks'],value]))+r'\\';assert row in ext,row;rows.append(row)
    targets='\n'.join(rows)+'\n'
    summary={'recomputed_analyses':list(rebuilt),'timing_rows_tex':timing,'cancellation_rows_tex':cancellation,'target_comparison_rows_tex':targets,'expanded_target_plot_data':{k:r['replication'][k] for k in ['state_rates','clean_rates']},'model_calls':0,'historical_empirical_tables':3}
    return summary
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=HERE/'reproduced');args=parser.parse_args()
    result=verify();out=args.output_dir;out.mkdir(exist_ok=True);(out/'supporting_tables.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'supporting_tables_recomputed':3,'analyses_checked':len(result['recomputed_analyses']),'model_calls':0}))
