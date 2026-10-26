"""Verify saved evidence and reproduce the paper's principal tables without model calls."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from build_paired_effects import produce as paired
from build_principal_tables import produce as tables
from build_exploratory_followup import produce as exploratory
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=HERE/'reproduced');args=ap.parse_args()
    checks=[['verify_supporting_results.py','--output-dir',str(args.output_dir)],['test_release_integrity.py'],['test_exploratory_followup.py'],['build_exploratory_followup.py','--check'],['test_paired_effects.py'],['build_results.py','--check'],['build_case_review.py','--check'],['build_policy_audit.py','--check'],['verify_policy_evidence_audit.py'],['build_paired_effects.py','--check'],['build_principal_tables.py','--check'],['build_manuscript.py','--check']]
    for check in checks:
        subprocess.run([sys.executable,str(HERE/check[0]),*check[1:]],cwd=ROOT,check=True)
    outputs={**paired(ROOT),**tables(ROOT),**exploratory(ROOT)}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,text in outputs.items():
        assert (HERE/name).read_text()==text,name
        (args.output_dir/name).write_text(text)
    report={'status':'passed','model_calls':0,'compact_tables':8,'supporting_main_tables':3,'paired_rows':560,'planned_tests_withheld':4,'unplanned_actor_contrasts':4,'checks':checks,'outputs_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in outputs.items()},'scope':'Principal compact-study tables, rule summary and explicitly exploratory actor tests. Three earlier main-text tables are recomputed from saved episodes and monitor scores; other historical checks remain separate. Environment and release-byte verification are recorded in the release README.'}
    (args.output_dir/'reproduction.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
