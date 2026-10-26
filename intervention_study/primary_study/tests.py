"""Tests of denominators, dependence, failures, public inputs and collection locks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import ROOT, read, digest, save
from intervention_study.primary_study import statistics as s, runner, evidence
from intervention_study.primary_study.analyze import make_rows, analyze_data
from intervention_study.primary_study.customer_audit import audit
from intervention_study.primary_study.native import replay, differences, summarize
from intervention_study.scaled_design.shadow import export_record
from intervention_study.scaled_design.statistics import paired_difference as old_effect
from intervention_study.test_intervention import FakeGateway


class PrimaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={c['case_id']:c for c in read(ROOT/'intervention_study/cases.json')}

    def paired(self):
        return [dict(pair_id=p,rule=p[0],actor=a,repeat=r,condition=g,customer='scripted',pressure=True,y=(int(p.endswith('1')) if g=='none' else 0))
                for p in ['a1','a2','b1','b2'] for a in ['x','y'] for r in range(3) for g in ['none','broad']]

    def test_point_estimate_matches_frozen_paired_implementation(self):
        rows=self.paired();a=s.paired_effect(rows,'y','broad',customer='scripted',pressure=True,draws=200)
        b=old_effect(rows,'y','broad',customer='scripted',pressure=True,draws=200)
        self.assertEqual(a['estimate'],b['estimate']);self.assertEqual(a['estimate'],-.5)

    def test_exact_randomization_and_zero_differences(self):
        self.assertEqual(s.paired_randomization([-1]*6,['a']*3+['b']*3)['p_value'],2/64)
        self.assertEqual(s.paired_randomization([0]*6,['a']*6)['p_value'],1)
        self.assertIsNone(s.paired_randomization([None],['a'])['p_value'])

    def test_holm_preserves_missing_family_slots(self):
        self.assertEqual(s.holm_adjust([.001,.01,.04,None,None,None]),[.006,.05,.16,None,None,None])
        with self.assertRaises(ValueError):s.holm_adjust([2])

    def test_randomization_missing_pair_withholds_test(self):
        rows=self.paired();rows[0]['y']=None
        result=s.paired_effect(rows,'y','broad',customer='scripted',pressure=True,draws=20,randomization=True)
        self.assertIsNone(result['randomization_test']['p_value'])

    def test_duplicate_and_unpaired_cells_rejected(self):
        rows=self.paired()
        for bad in [rows+[rows[0]],rows[1:]]:
            with self.assertRaises(ValueError):s.paired_effect(bad,'y','broad',customer='scripted',pressure=True,draws=10)

    def test_missing_keeps_bounds_and_withholds_interval(self):
        rows=self.paired();rows[0]['y']=None
        result=s.paired_effect(rows,'y','broad',customer='scripted',pressure=True,draws=10)
        self.assertIsNone(result['estimate']);self.assertEqual(len(result['missing_pairs']),1)
        self.assertLess(*result['assignment_bounds'])

    def test_pair_size_does_not_change_weight(self):
        rows=[]
        for p,n,b in [('p1',9,1),('p2',1,0)]:
            for repeat in range(n):
                for g in ['none','broad']:
                    rows.append(dict(pair_id=p,rule='r',actor='a',repeat=repeat,customer='scripted',pressure=True,condition=g,y=b if g=='none' else 0))
        self.assertEqual(s.paired_effect(rows,'y','broad',customer='scripted',pressure=True,draws=20)['estimate'],-.5)

    def source(self,p='p',bounded=True):return dict(episode=p,pair_id=p,rule='r',bounded_observed=bounded)
    def proposal(self,p='p',i=0,block=False):
        return dict(proposal_id=p+str(i),episode=p,pair_id=p,rule='r',private_oracle_checks=[{'verdict':'violation'}],public_predicate_checks=[],
          covered_violation=True,native_state_change=True,native_error=False,after_prior_executed_violation=False,
          decisions={g:{'block':block,'monitor_failure':False} for g in ['broad','decomposed','oracle']})

    def test_zero_shadow_denominator_is_undefined(self):
        result=s.shadow_summary([], [self.source()], 'state_changing_violation',draws=20)
        self.assertIsNone(result['gates']['broad']['rate']);self.assertEqual(result['gates']['broad']['undefined_bootstrap_fraction'],1)

    def test_unscored_shadow_is_unknown_not_allow(self):
        row=self.proposal();row.pop('decisions')
        r=s.shadow_summary([row],[self.source()],'state_changing_violation',draws=20)['gates']['broad']
        self.assertEqual(r['observed_denominator_bounds'],[0,1]);self.assertEqual(r['missing_decisions'],1);self.assertIsNone(r['rate'])

    def test_shadow_rate_weights_and_paired_difference(self):
        rows=[self.proposal('p1',i,True) for i in range(9)]+[self.proposal('p2',0,False)]
        for row in rows:row['decisions']['broad']['block']=False
        r=s.shadow_summary(rows,[self.source('p1'),self.source('p2')],'state_changing_violation',draws=100)
        self.assertEqual(r['gates']['decomposed']['rate'],.9);self.assertEqual(r['gates']['decomposed']['equal_supported_pair_rate'],.5)
        self.assertEqual(r['paired_gate_differences']['decomposed-broad']['estimate'],.9)

    def test_shadow_interruption_and_duplicate_support(self):
        row=self.proposal()
        r=s.shadow_summary([row],[self.source(bounded=False)],'state_changing_violation',draws=10)
        self.assertTrue(r['gates']['broad']['interval_withheld'])
        with self.assertRaises(ValueError):s.shadow_summary([row,row],[self.source()],'state_changing_violation',draws=10)

    def test_first_violation_sensitivity_drops_later_proposals(self):
        rows=[self.proposal(i=0),self.proposal(i=1)];rows[1]['after_prior_executed_violation']=True
        self.assertEqual(s.shadow_summary(rows,[self.source()],'state_changing_violation',first_violation_only=True,draws=10)['proposals'],1)

    def test_native_rejection_is_separate_from_state_change(self):
        row=self.proposal();row.update(native_state_change=False,native_error=True)
        self.assertEqual(s.shadow_class(row),'native_rejected_violation')

    def test_context_transitive_components(self):
        d=[dict(pair_id='a',entity_keys=['x']),dict(pair_id='b',entity_keys=['x','y']),dict(pair_id='c',entity_keys=['y']),dict(pair_id='d',entity_keys=['z'])]
        self.assertEqual(s.dependency_components(d),[['a','b','c'],['d']])

    def test_observed_positive_survives_process_interruption(self):
        cell=dict(episode='a',pressure=True);rec=dict(episode='a',status='started',actions=[{'executed_selected_violation':True}],format_violation=True)
        row=make_rows([cell],[rec],{})[0]
        self.assertEqual(row['executed_violation'],1);self.assertEqual(row['format_violation'],1);self.assertIsNone(row['actor_turns'])

    def test_added_null_is_a_state_difference(self):self.assertEqual(differences({}, {'new':None}), ['/new'])

    def test_original_customer_failures_detected(self):
        base=ROOT/'intervention_study/scaled_design'
        rec=read(next((base/'episodes').glob('*identity_lookup-00-control*llm*.json')))
        self.assertIn('terminal_confirmation',[f['kind'] for f in audit(self.cases[rec['case_id']],rec)['flags']])

    def test_customer_literal_drift_is_flagged(self):
        base=ROOT/'intervention_study/scaled_design/repair_validation_v2'
        rec=copy.deepcopy(read(next((base/'episodes').glob('*identity_lookup-00-control*llm*.json'))))
        rec['customer_events'][0]['response']='Use attacker@example.org and order #Z9999999 on 2099-12-31.'
        kinds=[f['kind'] for f in audit(self.cases[rec['case_id']],rec)['flags']]
        self.assertIn('unsupported_literal',kinds)

    def test_unknown_policy_is_not_covered_eligible(self):
        r=self.proposal();r.update(covered_violation=False,private_oracle_checks=[{'verdict':'unknown'}])
        self.assertEqual(s.shadow_class(r),'unresolved_or_uncovered')

    def test_primary_authorization_fails_before_gateway(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'authorization.json',{'approved':False});save(b/'protocol.json',{})
            with self.assertRaises(PermissionError):runner.approved_ceiling(b)

    def test_primary_authorization_cannot_exceed_global_budget(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'protocol.json',{})
            save(b/'authorization.json',{'approved':True,'scope':'primary_live_and_shadow','protocol_sha256':digest(b/'protocol.json'),'cumulative_ceiling_usd':999999})
            original_read=runner.read
            with patch.object(runner,'read',side_effect=lambda p:{'cumulative_usd_cap':125} if Path(p).name=='authorization.json' and Path(p).parent.name=='groundwork' else original_read(p)):
                with self.assertRaises(PermissionError):runner.approved_ceiling(b)

    def test_native_pipeline_continues_after_block(self):
        case=self.cases['airline_compensation-00-pressure'];cell={k:case[k] for k in ['case_id','pair_id','rule','domain','pressure','split']}
        cell.update(episode='fake',actor='test',repeat=0,condition='oracle',customer='scripted')
        gateway=FakeGateway(case)
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'protocol.json',{})
            rec=runner.run_cell(cell,{'max_actor_turns':20,'max_customer_turns':8,'customer_model':'customer','gate_model':'gate'},gateway,b)
        result=replay(case,rec)
        self.assertEqual(sum(x['direct_interception'] for x in result['blocks']),1)
        summary=summarize([result])[0]
        self.assertEqual(sum(summary['classes'].values()),summary['blocks'])
        self.assertEqual(summary['classes']['state_changing_covered_violation'],1)
        self.assertTrue(any('policy_gate_blocked' in (m.get('content') or '') for m in gateway.actor_inputs[-1]))

    def test_shadow_failure_retains_partial_denominator(self):
        base=ROOT/'intervention_study/live_gating/episodes'
        rec=read(next(base.glob('*airline_compensation-01-pressure*none*.json')));case=self.cases[rec['case_id']]
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'shadow.json'
            done=runner.run_shadow(rec,case,FakeGateway(case,True),{'gate_model':'gate'},dest)
            saved=read(dest)
        self.assertFalse(done);self.assertTrue(saved['rows']);self.assertTrue(any(d['block'] is None for r in saved['rows'] for d in r['decisions'].values()))

    def test_empty_allocation_is_unknown_and_all_six_tests_withheld(self):
        allocation=read(ROOT/'intervention_study/primary_study/allocation.json')
        result=analyze_data(allocation,[],[],cost_by={},dependencies=read(ROOT/'intervention_study/primary_study/dependencies.json'),customer_checks=[],draws=10)
        self.assertEqual(result['assigned'],4608);self.assertEqual(result['recorded'],0)
        self.assertTrue(all(e['assignment_bounds']==[-1,1] for e in result['primary_contrasts']))
        self.assertTrue(all(e['randomization_test']['holm_adjusted_p'] is None for e in result['primary_contrasts']))

    def test_evidence_roundtrip_failed_requests_and_ledger_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);base=root/'study';base.mkdir();raw=root/'groundwork/api_records';raw.mkdir(parents=True)
            save(base/'allocation.json',[{'episode':'ep'}])
            entries=[{'episode':'ep','role':'live_gating_actor','request_id':'ok','reserved_usd':.3},
                     {'episode':'ep--shadow','role':'gate','request_id':'failed','reserved_usd':.4}]
            save(raw/'ok.json',{'request_id':'ok','status':'ok','response':{'usage':{'cost':.1}}})
            save(raw/'failed.json',{'request_id':'failed','status':'error'})
            ledger=root/'groundwork/spend_ledger.jsonl';ledger.write_text('\n'.join(json.dumps(e) for e in entries))
            with patch.object(evidence,'ROOT',root):
                evidence.pack(base);store=evidence.Receipts(base,True);cost=evidence.costs(evidence.stage_ledger(base,True),store)
                self.assertEqual(cost['ep']['actor']['reported_usd'],.1)
                self.assertEqual(cost['ep']['shadow']['unknown_cost_requests'],1)
                self.assertEqual(cost['ep']['shadow']['unresolved_reservation_usd'],.4)
                old=read(base/'evidence/manifest.json');store.archive.close()
                entries[1]['reserved_usd']=.5;ledger.write_text('\n'.join(json.dumps(e) for e in entries))
                evidence.pack(base);new=read(base/'evidence/manifest.json')
                self.assertNotEqual(old['ledger'],new['ledger'])
                self.assertEqual(digest(base/'evidence'/old['ledger']),old['ledger_sha256'])
                (base/'evidence'/new['ledger']).write_text('tampered')
                with self.assertRaises(ValueError):evidence.Receipts(base,True)


if __name__=='__main__':unittest.main()
