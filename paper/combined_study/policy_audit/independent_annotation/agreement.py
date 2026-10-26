"""Compute pre-reconciliation agreement; never substitute labels for missing forms."""
import csv, json, sys
from collections import Counter

def load(path):
    rows=list(csv.DictReader(open(path)))
    assert len(rows)==95 and len({r['case_id'] for r in rows})==95,'Expected 95 unique cases'
    for r in rows:
        assert r['permission'] in ['required','permitted','forbidden','uncertain'],'Missing/invalid permission'
        assert r['block_justification'] in ['justified','unnecessary','uncertain'],'Missing/invalid block judgment'
        assert r['format'] in ['compliant','breach','uncertain'],'Missing/invalid format label'
        assert all(r[k].strip() for k in ['policy_clause','prefix_evidence','rationale']),'Missing supporting evidence'
    return {r['case_id']:r for r in rows}

def agreement(a,b):
    assert len(a)==len(b) and len(a)>0
    n=len(a);matrix=Counter(zip(a,b));ca,cb=Counter(a),Counter(b)
    observed=sum(x==y for x,y in zip(a,b))/n
    expected=sum(ca[k]*cb[k] for k in ca.keys()|cb.keys())/n**2
    return {'n':n,'agreement':observed,'kappa':(observed-expected)/(1-expected) if expected<1 else None,'kappa_undefined':expected==1,'matrix':[{'annotator_1':x,'annotator_2':y,'n':c} for (x,y),c in sorted(matrix.items())]}

if __name__=='__main__':
    a,b=map(load,sys.argv[1:]);assert set(a)==set(b),'Case mismatch';ids=sorted(a)
    print(json.dumps({k:agreement([a[i][k] for i in ids],[b[i][k] for i in ids]) for k in ['permission','block_justification']},indent=2))
