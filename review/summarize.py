"""Validate two independent form exports and report agreement before reconciliation.

Run privately: python review/summarize.py R1-submission.json R2-submission.json
Optional --coordinator-key path unlocks prespecified subgroup counts; never publish responses.
"""
import argparse, collections, csv, hashlib, io, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
FIELDS=['case_id','permission','block_justification','format','policy_clause','prefix_evidence','rationale']
CHOICES={'permission':['required','permitted','forbidden','uncertain'],'block_justification':['justified','unnecessary','uncertain'],'format':['compliant','breach','uncertain']}
def csv_text(rows):
    def cell(x):
        s=str(x)
        if s.startswith(('=','+','@','-')): s="'"+s
        return '"'+s.replace('"','""')+'"'
    return '\r\n'.join(','.join(cell(x) for x in row) for row in [FIELDS]+[[r[k] for k in FIELDS] for r in rows])+'\r\n'
def load(path):
    d=json.loads(Path(path).read_text()); manifest=json.loads((R/'review/packet_manifest.json').read_text())
    assert d['packet_sha256']==manifest['packet_sha256'],'Wrong packet'
    assert d['independent'] is True and d['attest'] is True,'Independent declarations missing'
    assert isinstance(d['reviewer'],str) and d['reviewer'].strip() and isinstance(d['experience'],str) and d['experience'].strip(),'Reviewer profile missing'
    assert d['relationship'] in ['external','coauthor_not_designer','designer'],'Relationship missing'
    rows=d['rows']; assert d['case_count']==99 and len(rows)==99,'Expected all 99 cases'
    assert {r['case_id'] for r in rows}=={f'CASE{i:03}' for i in range(1,100)},'Case mismatch'
    for r in rows:
        assert set(r)==set(FIELDS),'Unexpected response fields'
        for k,opts in CHOICES.items(): assert r[k] in opts,'Invalid label'
        for k in FIELDS[4:]: assert isinstance(r[k],str) and r[k].strip(),'Evidence missing'
    raw=csv_text(rows).encode(); assert hashlib.sha256(raw).hexdigest()==d['csv_sha256'],'Response checksum mismatch'
    csv_path=Path(path).with_name(Path(path).name.replace('-submission.json','.csv'))
    assert csv_path.is_file() and csv_path.read_bytes()==raw,'Matching CSV required next to submission JSON'
    return d,{r['case_id']:r for r in rows}
def agreement(a,b):
    n=len(a);ca,cb=collections.Counter(a),collections.Counter(b)
    po=sum(x==y for x,y in zip(a,b))/n;pe=sum(ca[k]*cb[k] for k in ca.keys()|cb.keys())/n**2
    return {'n':n,'raw_agreement':po,'cohen_kappa':(po-pe)/(1-pe) if pe<1 else None,'uncertain_is_category':True,'matrix':[{'reviewer_1':x,'reviewer_2':y,'n':v} for (x,y),v in sorted(collections.Counter(zip(a,b)).items())]}
def group(ids,a,b):
    return {'n':len(ids),'agreement':{k:agreement([a[i][k] for i in ids],[b[i][k] for i in ids]) for k in CHOICES},'block_judgments':{'reviewer_1':dict(collections.Counter(a[i]['block_justification'] for i in ids)),'reviewer_2':dict(collections.Counter(b[i]['block_justification'] for i in ids)),'agreed':dict(collections.Counter(a[i]['block_justification'] for i in ids if a[i]['block_justification']==b[i]['block_justification'])),'disagreements':sum(a[i]['block_justification']!=b[i]['block_justification'] for i in ids)}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('first');ap.add_argument('second');ap.add_argument('--coordinator-key',type=Path);args=ap.parse_args()
    p,a=load(args.first);q,b=load(args.second);assert p['reviewer']!=q['reviewer'],'Distinct reviewer codes required'
    groups={'original_95':[f'CASE{i:03}' for i in range(1,96)],'supplementary_4':[f'CASE{i:03}' for i in range(96,100)]}
    if args.coordinator_key:
        key=json.loads(args.coordinator_key.read_text())['key'];assert {r['case_id'] for r in key}==set(a) and len(key)==99
        groups['unresolved_65']=[r['case_id'] for r in key if r.get('audit_category','')=='unresolved']
        # Some coordinator versions use the full category name.
        if not groups['unresolved_65']: groups['unresolved_65']=[r['case_id'] for r in key if 'unresolved' in r.get('audit_category','')]
        groups['completion_loss_blocks_20']=[r['case_id'] for r in key if r['completion_loss_block']]
        assert len(groups['unresolved_65'])==65 and len(groups['completion_loss_blocks_20'])==20,'Coordinator strata mismatch'
    print(json.dumps({'status':'independent judgments; not adjudicated truth','reviewer_profiles':[{k:d[k] for k in ['reviewer','experience','relationship']} for d in [p,q]],'groups':{k:group(v,a,b) for k,v in groups.items()},'limitations':'Do not extrapolate unweighted sample counts to all blocks. Preserve uncertainty and disagreements; any reconciliation must be documented separately. Codes and attestations do not independently authenticate human identity.'},indent=2))
if __name__=='__main__':main()
