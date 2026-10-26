"""Render the measurement chain and its distinct live and offline paths."""
from pathlib import Path
import os, tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'manuscript-plot-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
out=Path(__file__).resolve().parent
fig,ax=plt.subplots(figsize=(10,3.1));ax.set_xlim(0,10);ax.set_ylim(0,3.1);ax.axis('off')
plt.rcParams['pdf.fonttype']=42
boxes=[(.12,'Actor proposal\n+ visible prefix'),(2.12,'Monitor warning\nagainst a target'),(4.12,'Gate decision\nallow / block'),(6.12,'Native execution\nchange / reject'),(8.12,'Final outcome\n+ policy checks')]
for x,label in boxes:
 ax.add_patch(FancyBboxPatch((x,1.72),1.72,.72,boxstyle='round,pad=0.06,rounding_size=0.05',facecolor='#eaf1f7',edgecolor='#284d69',linewidth=1.1))
 ax.text(x+.86,2.08,label,ha='center',va='center',fontsize=12)
for x1,x2 in [(1.9,2.04),(3.9,4.04),(5.9,6.04),(7.9,8.04)]:ax.add_patch(FancyArrowPatch((x1,2.08),(x2,2.08),arrowstyle='-|>',mutation_scale=10,color='#284d69'))
ax.text(5.99,2.61,'allow',ha='center',fontsize=11,color='#284d69')
for x,t in [(2.98,'RQ1  Detection'),(6.98,'RQ2  Added protection'),(8.98,'RQ3  Task outcome')]:ax.text(x,2.93,t,ha='center',va='center',fontsize=11,fontweight='bold',color='#284d69')
ax.plot([4.98,4.98,.98,.98],[1.65,1.13,1.13,1.65],color='#8a5a28',lw=1.1)
ax.annotate('',xy=(.98,1.65),xytext=(.98,1.48),arrowprops=dict(arrowstyle='-|>',color='#8a5a28',lw=1.1))
ax.text(2.98,1.28,'block feedback: actor may continue',ha='center',fontsize=11,color='#8a5a28')
ax.add_patch(FancyBboxPatch((5.85,.15),3.85,.85,boxstyle='round,pad=0.06,rounding_size=0.05',facecolor='#f6f3ed',edgecolor='#8a5a28',linestyle='--',linewidth=1.1))
ax.text(7.78,.6,'Offline replay of the proposed action\nin its saved preceding state\n48 violating changes; 26 native rejections',ha='center',va='center',fontsize=11)
ax.plot([.46,.46,5.77],[1.65,.6,.6],color='#8a5a28',lw=1,ls='--')
ax.annotate('',xy=(5.79,.6),xytext=(5.6,.6),arrowprops=dict(arrowstyle='-|>',color='#8a5a28',lw=1))
ax.text(3.05,.39,'one transition; no counterfactual dialogue',ha='center',fontsize=11,color='#8a5a28')
fig.subplots_adjust(left=0,right=1,bottom=0,top=1)
fig.savefig(out/'evaluation_flow.pdf',metadata={'Creator':'Matplotlib','Author':'','CreationDate':None,'ModDate':None})
fig.savefig(out/'evaluation_flow.png',dpi=180)
