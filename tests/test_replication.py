import copy,itertools,json
from replication.prepare import build
from replication.policy_lab import oracle,independent_rule
from replication.common import BASE

def test_complete_remaining_test_allocation():
 rows=build();assert len(rows)==42
 assert len({r['task_group'] for r in rows})==42
 assert sum(r['domain']=='airline' for r in rows)==11
 assert sum(r['domain']=='retail' for r in rows)==31

def test_policy_rules_exhaustive_equivalence_and_boundaries():
 for cabin,insurance,reason,created,status in itertools.product(['economy','basic_economy','business'],['yes','no'],['health','weather','change of plan'],['2024-05-01T12:00:00','2024-05-14T14:59:59','2024-05-14T15:00:00','2024-05-14T15:00:01','2024-05-15T15:00:00','2024-05-16T00:00:00'],['available','cancelled','flying','landed']):
  facts=dict(cabin=cabin,insurance=insurance,reason=reason,created_at=created,statuses=[status])
  assert oracle(facts)==independent_rule(facts)
  if status in ['flying','landed']:assert not oracle(facts)
 # Exact 24-hour boundary deliberately excluded from constructed cases.
 f=dict(cabin='economy',insurance='no',reason='change of plan',created_at='2024-05-14T15:00:01',statuses=['available'])
 assert oracle(f);f['created_at']='2024-05-14T14:59:59';assert not oracle(f)

def test_controlled_pairs_preserve_action_and_hide_labels():
 rows=json.loads((BASE/'policy_lab/cases.json').read_text());assert len(rows)==48
 pairs={}
 for r in rows:
  pairs.setdefault(r['pair'],[]).append(r)
  assert r['native_cancellation_executed'] and not r['contract_violation']
  assert set(r['public_input'])=={'policy','tools','conversation_prefix'}
 for pair in pairs.values():
  assert len(pair)==2 and {r['eligible'] for r in pair}=={True,False}
  assert pair[0]['public_input']['conversation_prefix'][-1]==pair[1]['public_input']['conversation_prefix'][-1]
  assert pair[0]['public_input']['policy']==pair[1]['public_input']['policy']

def test_monitor_missingness_keeps_episode_and_first_alert_distinct():
 from replication.analyze import summarize
 r=summarize([{'event_index':0,'status':'missing','risk':None},{'event_index':2,'status':'scored','risk':.8}],.5)
 assert r['any_identified'] and r['any_alert'] and not r['first_identified']
 r=summarize([{'event_index':0,'status':'scored','risk':.8},{'event_index':2,'status':'missing','risk':None}],.5)
 assert r['first_identified'] and r['first_alert']==0
 r=summarize([{'event_index':0,'status':'scored','risk':.1},{'event_index':2,'status':'missing','risk':None}],.5)
 assert not r['any_identified'] and not r['first_identified']
