"""Build a self-contained reviewer form using only the blinded inputs and rubric."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
A=R/'paper/combined_study/policy_audit/independent_annotation'
cases=[json.loads(line) for n in ['cases.jsonl','supplementary_cases.jsonl'] for line in (A/n).read_text().splitlines()]
assert len(cases)==99 and len({r['case_id'] for r in cases})==99
assert all(set(r)=={'case_id','public_input'} for r in cases)
assert all(set(r['public_input'])=={'policy','tools','conversation_prefix','current_write'} for r in cases)
# Fixed shuffled presentation keeps supplementary cases from forming an obvious final group.
cases.sort(key=lambda c:hashlib.sha256(('review-20261026:'+c['case_id']).encode()).hexdigest())
rubric=(A/'rubric.md').read_text()+'\n\nDelivery amendment, 26 October 2026: This form includes the original 95 cases plus four supplementary cases, for 99 total. Apply the same rubric to every case. The original sample and supplementary cases will be analyzed separately. No labels were collected before this amendment.\n'
payload=json.dumps({'cases':cases,'rubric':rubric},ensure_ascii=False,sort_keys=True,separators=(',',':'))
packet={'cases':cases,'rubric':rubric,'sha256':hashlib.sha256(payload.encode()).hexdigest()}
text=(R/'review/form-template.html').read_text()
for key,value in {'CSS':(R/'review/form.css').read_text(),'CORE':(R/'review/core.js').read_text(),'APP':(R/'review/app.js').read_text(),'PACKET':json.dumps(packet,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')}.items():text=text.replace('__'+key+'__',value)
assert '__PACKET__' not in text
(R/'docs/review/index.html').write_text(text)
(R/'docs/.nojekyll').touch()
(R/'review/packet_manifest.json').write_text(json.dumps({'case_count':99,'core_cases':95,'supplementary_cases':4,'packet_sha256':packet['sha256'],'inputs_sha256':{n:hashlib.sha256((A/n).read_bytes()).hexdigest() for n in ['cases.jsonl','supplementary_cases.jsonl','rubric.md']},'form_sha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'Only blinded public inputs and rubric are embedded. No coordinator mappings, current gate decisions, audit classifications or final outcomes are added.'},indent=2)+'\n')
print('Built 99-case self-contained review form:',packet['sha256'])
