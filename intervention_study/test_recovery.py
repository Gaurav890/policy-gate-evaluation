"""Regression checks for premature customer stop and network circuit breaking."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from unittest import TestCase,main
from intervention_study.test_intervention import InterventionTests,FakeGateway
from intervention_study import runner_v2, runtime_guarded
class RecoveryTests(InterventionTests):
    def run_case(self,*args,**kwargs):
        from intervention_study import test_intervention
        with patch.object(test_intervention,'runner',runner_v2):
            # Test harness writes a dummy v1 protocol; provide v2 via digest interception only in tests.
            real_digest=runner_v2.digest
            with patch.object(runner_v2,'digest',side_effect=lambda v:real_digest(v.parent/'protocol.json') if isinstance(v,Path) and v.name=='protocol_v2.json' else real_digest(v)):
                return super().run_case(*args,**kwargs)
    def test_confirmation_is_not_termination(self):
        original=FakeGateway.complete
        def complete(g,model,messages,**kw):
            message,receipt=original(g,model,messages,**kw)
            if kw['role']=='pressure_customer' and not getattr(g,'already_confirmed',False):
                g.already_confirmed=True;message['content']=json.dumps({'response':'Yes, please proceed.','stop':True,'pushback':False})
            return message,receipt
        with patch.object(FakeGateway,'complete',complete):rec,_=self.run_case(self.case('airline_cancellation',False))
        self.assertTrue(rec['customer_events'][0]['stop_overridden_for_confirmation'])
        self.assertEqual(len(rec['customer_events']),2)
    def test_confirmation_allows_the_pending_write_to_happen(self):
        original=FakeGateway.complete
        def complete(g,model,messages,**kw):
            if kw['role']=='pressure_actor':
                seen=[m for m in messages if m['role']=='tool']
                case=self.case('airline_cancellation',False)
                if len(seen)==len(case['fixture_reads']) and not getattr(g,'confirmation_requested',False):
                    g.confirmation_requested=True
                    return {'role':'assistant','content':'Please confirm: should I cancel the reservation?'},{'request_id':'confirmation-request'}
            message,receipt=original(g,model,messages,**kw)
            if kw['role']=='pressure_customer' and not getattr(g,'confirmed_pending_write',False):
                g.confirmed_pending_write=True;message['content']=json.dumps({'response':'Yes, please proceed.','stop':True,'pushback':False})
            return message,receipt
        with patch.object(FakeGateway,'complete',complete):rec,g=self.run_case(self.case('airline_cancellation',False))
        self.assertTrue(rec['control_reference_state_match'])
        self.assertEqual(len(rec['customer_events']),2)
        self.assertTrue(rec['customer_events'][0]['stop_overridden_for_confirmation'])
    def test_preflight_failure_never_calls_inference(self):
        import socket
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'stop.json';g=object.__new__(runtime_guarded.GuardedGateway)
            with patch.object(runtime_guarded,'STOP',path),patch.object(runtime_guarded.socket,'getaddrinfo',side_effect=socket.gaierror('offline')),patch.object(runtime_guarded.Gateway,'complete') as inference:
                with self.assertRaises(runtime_guarded.GuardStopped):g.complete('test',[])
                inference.assert_not_called();self.assertTrue(path.exists())
    def test_shared_stop_prevents_network_or_spend(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'stop.json';path.write_text('{}')
            g=object.__new__(runtime_guarded.GuardedGateway)
            with patch.object(runtime_guarded,'STOP',path),patch.object(runtime_guarded.socket,'getaddrinfo') as dns:
                with self.assertRaises(runtime_guarded.GuardStopped):g.complete('test',[])
                dns.assert_not_called()
if __name__=='__main__':main()
