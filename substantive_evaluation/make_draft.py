"""Assemble the edited review manuscript without overwriting editorial prose.

Statistical generators write paper/generated and their own reports. The readable
manuscript lives in paper/editorial; reconcile new findings there explicitly.
"""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'paper'; B=R/'substantive_evaluation'
source=P/'editorial/manuscript.tex'
text=source.read_text()
for relative in re.findall(r"\\input\{([^}]+)\}",text):
    assert (P/relative).is_file(), relative
(P/'expanded_review_draft.tex').write_text(text)
files=[source,*sorted((P/'editorial').glob('*.tex'))]
provenance={'editorial_source':'paper/editorial/manuscript.tex',
 'draft_source':'paper/expanded_review_draft.tex',
 'status':'Anonymous editorial revision; see submission/release_status.json for verified package status',
 'source_hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
 'analysis_sha256':hashlib.sha256((B/'analysis.json').read_bytes()).hexdigest()}
(B/'draft_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Assembled expanded draft from preserved editorial source')
