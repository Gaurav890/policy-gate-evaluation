import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'substantive_evaluation';a=json.loads((B/'analysis.json').read_text());fig,ax=plt.subplots(figsize=(7.1,3.4));models=['gemini','gptmini'];targets=['broad','interaction','substantive'];colors=['#68788d','#dc9740','#147d76']
for j,t in enumerate(targets):
 rows=[next(x for x in a['conditional_negative_alerts'] if x['cohort']=='substantive_evaluation/episodes' and x['subset']=='interaction_clean_no_policy_tool_discrepancy' and x['model']==m and x['target']==t) for m in models]
 for i,r in enumerate(rows):
  if r['alert_rate_bounds'] is None:continue
  lo,hi=r['alert_rate_bounds'];x=i+(j-1)*.23
  ax.bar(x,lo*100,width=.2,color=colors[j],label=t if i==0 else None)
  if hi>lo:ax.bar(x,(hi-lo)*100,bottom=lo*100,width=.2,facecolor='none',edgecolor=colors[j],hatch='///')
  ax.text(x,hi*100+2,f"{r['alert_count_bounds'][0]}/{r['negative_episodes']}",ha='center',fontsize=8)
ax.set_xticks([0,1],['Gemini 3.8 Flash','GPT-5.4 Mini']);ax.set_ylabel('Episodes with an alert (%)');ax.set_ylim(0,113);ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.2));fig.tight_layout()
fig.savefig(B/'selected_negative_alerts.pdf',bbox_inches='tight');fig.savefig(B/'selected_negative_alerts.png',dpi=150,bbox_inches='tight')
