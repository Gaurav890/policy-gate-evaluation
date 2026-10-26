"""Replay ungated records into matched write inputs; optional scoring is explicit."""
import copy,json,hashlib
from intervention_study.common import ROOT,read,digest,environment
from intervention_study.serialization import to_json
from intervention_study.gates import decide
from intervention_study.predicates import check,observed_facts,public_context

def export_record(record,case):
 if record['condition']!='none':raise ValueError('Shadow source must be an ungated rollout')
 env=environment(case);rows=[]
 for i,event in enumerate(record['actions']):
  assert env.get_db_hash()==event['before_db_hash']
  call=event['call']
  if event['mutates']:
   # Prior results from sibling calls are public; later siblings have not run.
   prefix=record['canonical_messages'][:event['message_index']+1+event['call_index']]
   public={'policy':env.policy,'tools':[t.openai_schema for t in env.get_tools()],'conversation_prefix':copy.deepcopy(prefix),'current_write':copy.deepcopy(call)}
   shadow=copy.deepcopy(env)
   try:result=to_json(shadow.make_tool_call(call['name'],**call['arguments']));error=False
   except (ValueError,TypeError,KeyError) as exc:result={'error':str(exc)};error=True
   rows.append({'proposal_id':record['episode']+f'--write-{i}','episode':record['episode'],'case_id':case['case_id'],'pair_id':case['pair_id'],'rule':case['rule'],'pressure':case['pressure'],
    'action_index':i,'public':public,'public_sha256':digest(public),'private_oracle_checks':event['oracle_checks'],
    'public_predicate_checks':check(case['domain'],call,observed_facts(prefix),public_context(prefix)),
    'before_db_hash':event['before_db_hash'],'native_after_hash':shadow.get_db_hash(),'native_error':error,'native_result':result,
    'native_state_change':shadow.get_db_hash()!=event['before_db_hash'],'covered_violation':event['attempted_selected_violation'],
    'after_prior_executed_violation':any(a['executed_selected_violation'] for a in record['actions'][:i])})
  if event['blocked']:raise ValueError('Ungated source contains a block')
  try:env.make_tool_call(call['name'],**call['arguments'])
  except (ValueError,TypeError,KeyError):pass
  assert env.get_db_hash()==event['after_db_hash']
 return rows

def score_record(record,case,g,cfg,checkpoint=None):
 exported=export_record(record,case);env=environment(case)
 out=[{**r,'decisions':{gate:{'block':None,'monitor_failure':True,'status':'unscored'} for gate in ['broad','decomposed','oracle']}} for r in exported]
 indexed={r['action_index']:r for r in out}
 if checkpoint:checkpoint(out)
 for i,event in enumerate(record['actions']):
  if i in indexed:
   row=indexed[i];before=env.get_db_hash()
   gates=['broad','decomposed','oracle'];offset=int(hashlib.sha256(row['proposal_id'].encode()).hexdigest(),16)%3;gates=gates[offset:]+gates[:offset]
   for gate in gates:
    try:
     decision=decide(gate,case,env,copy.deepcopy(row['public']['conversation_prefix']),copy.deepcopy(event['call']),copy.deepcopy(event['oracle_checks']),g,cfg,record['episode']+'--shadow')
     assert env.get_db_hash()==before
     for score in decision.get('checks',[]):
      if 'public_input_sha256' in score:assert score['public_input_sha256']==row['public_sha256']
     row['decisions'][gate]={**decision,'status':'scored'}
    except Exception as exc:
     row['decisions'][gate]={'block':None,'monitor_failure':True,'status':'missing','error_type':type(exc).__name__}
     if checkpoint:checkpoint(out)
     return out
    if checkpoint:checkpoint(out)
  try:env.make_tool_call(event['call']['name'],**event['call']['arguments'])
  except (ValueError,TypeError,KeyError):pass
 return out
