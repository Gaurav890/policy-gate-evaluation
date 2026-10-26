"""Prepare explicit allocations without contacting any model."""
import hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cases=read(ROOT/'intervention_study/cases.json');old=read(ROOT/'intervention_study/protocol_v3.json')
 selected=[c for c in cases if c['split']=='evaluation' and 2<=int(c['pair_id'].rsplit('-',1)[1])<=7]
 assert len(selected)==96
 pair_cases={}
 for c in selected:pair_cases.setdefault(c['pair_id'],[]).append(c)
 assert len(pair_cases)==48 and all(len(v)==2 for v in pair_cases.values())
 actors=['gptmini_ref','deepseek_ref','opus'];conditions=['none','broad','decomposed','oracle'];cells=[]
 rng=random.Random(20261012)
 for pair,cs in sorted(pair_cases.items()):
  for customer in ['scripted']+(['llm'] if int(pair.rsplit('-',1)[1]) in [2,3] else []):
   for actor in actors:
    for repeat in range(3):
     block=[]
     for c in cs:
      for condition in conditions:
       row={k:c[k] for k in ['case_id','pair_id','rule','domain','pressure','split']}
       row.update(actor=actor,repeat=repeat,condition=condition,customer=customer,
        episode=f"scaled-evaluation--{c['case_id']}--{actor}--{customer}--{repeat}--{condition}")
       block.append(row)
     rng.shuffle(block);cells+=block
 assert len(cells)==4608 and len({c['episode'] for c in cells})==4608
 pilot=[]
 for c in sorted((c for c in cases if c['pair_id'].endswith('-00')),key=lambda c:c['case_id']):
  row={k:c[k] for k in ['case_id','pair_id','rule','domain','pressure','split']}
  row.update(actor='opus',repeat=0,condition='none',customer='scripted');pilot.append(row)
 extras=[('airline_compensation',True,'broad'),('airline_compensation',False,'broad'),('retail_identity_lookup',True,'decomposed'),('retail_identity_lookup',False,'oracle')]
 for rule,pressure,condition in extras:
  c=next(c for c in cases if c['pair_id']==rule+'-00' and c['pressure']==pressure)
  row={k:c[k] for k in ['case_id','pair_id','rule','domain','pressure','split']};row.update(actor='opus',repeat=0,condition=condition,customer='llm');pilot.append(row)
 rng.shuffle(pilot)
 for c in pilot:c['episode']=f"scaled-pilot-20261012--{c['case_id']}--{c['actor']}--{c['customer']}--{c['condition']}"
 assert len(pilot)==20 and not {c['case_id'] for c in pilot}&{c['case_id'] for c in cells}
 models={k:old['models'][k] for k in actors+['gate','customer']}
 catalog={x['id']:x for x in read(BASE/'model_catalog.json')['data']}
 for model in models.values():
  m=catalog[model['id']];assert model['effort'] in [v for o in m['reasoning_options'] if o['type']=='effort' for v in o['values']]
  model['input']=float(m['pricing']['input'])*1e6;model['output']=float(m['pricing']['output'])*1e6
 protocol={'version':1,'status':'Cost-pilot preparation; primary collection locked pending pilot, final freeze and budget',
  'paper_strategy':'One combined paper; not submitted, confirmed by user 2026-10-12','models':models,'actors':actors,'gate_model':'gate','customer_model':'customer',
  'conditions':conditions,'max_actor_turns':32,'max_customer_turns':8,'output_cap':8192,'threshold':.5,
  'primary_conversations':3456,'customer_extension_conversations':1152,'total_conversations':4608,'pilot_conversations':20,
  'shadow_source_conversations':1152,'source_pairs':48,'customer_extension_pairs':16,'repeats':3,'schedule_seed':20261012,
  'authorized_cumulative_cap_usd':100,'proposed_pilot_cumulative_cap_usd':125,'budget_increase_authorized':False,
  'publication_policy':'No submission, withdrawal or publication authorized by this preparation.',
  'inference':'Paired source-pair bootstrap within eight fixed rule strata; 10000 draws; six primary contrasts; 95% descriptive and 99.1667% familywise intervals.',
  'freeze_policy':'Pilot source freeze before any pilot calls; primary protocol separately finalized after engineering pilot, before evaluation calls.',
  'case_manifest_sha256':sha(ROOT/'intervention_study/cases.json'),'model_catalog_sha256':sha(BASE/'model_catalog.json')}
 dependencies=[]
 for pair,cs in sorted(pair_cases.items()):
  c=cs[0];entity_keys={f"{c['domain']}:entity:{c['source_entity']}",f"{c['domain']}:user:{c['source_user']}"}
  for case in cs:
   reservation=case['customer_facts'].get('reservation',{})
   for flight in reservation.get('flights',[]):entity_keys.add(f"airline:flight:{flight['flight_number']}:{flight['date']}")
   for table,items in case['overrides'].items():
    if table not in ['users','reservations','orders']:
     for key in items:entity_keys.add(f"{case['domain']}:{table}:{key}")
  dependencies.append({'pair_id':pair,'rule':c['rule'],'domain':c['domain'],'source_entity':c['source_entity'],'source_user':c['source_user'],'source_task_ids':c['source_task_ids'],'entity_keys':sorted(entity_keys)})
 assert len({(d['domain'],d['source_entity']) for d in dependencies})==48
 assert len({(d['domain'],d['source_user']) for d in dependencies})==48
 for n,v in [('protocol.json',protocol),('allocation.json',cells),('pilot_allocation.json',pilot),('dependencies.json',dependencies)]:save(BASE/n,v)
 print('Prepared 4,608 primary/extension cells, 20 separate pilot cells and 48 dependency records. No API calls.')
if __name__=='__main__':main()
