import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
import gateway_v2 as g

class Opener:
    def __init__(self, outcomes): self.outcomes=iter(outcomes);self.requests=[]
    def open(self,req,timeout):
        self.requests.append(json.loads(req.data))
        value=next(self.outcomes)
        if isinstance(value,Exception):raise value
        return io.BytesIO(json.dumps(value).encode())

def error(code,header='0'):
    return urllib.error.HTTPError('https://example.invalid',code,'failure',{'retry-after':header},io.BytesIO(b'{"error":"secret-key-1234567890"}'))

def good():
    return {'usage':{'prompt_tokens':5,'completion_tokens':1,'cost':0.00002},'choices':[{'message':{'content':'ok'},'finish_reason':'stop'}]}

class RetryTests(unittest.TestCase):
    def client(self,tmp,opener,cap=30):
        with patch.object(g,'load_study_key',return_value='secret-key-1234567890'):
            client=g.Gateway(g.Budget(Path(tmp)/'ledger.jsonl',ceiling=cap),opener=opener,sleep=lambda _:None)
        client.records_dir=Path(tmp)/'records'
        return client
    def test_retry_preserves_payload_and_both_reservations(self):
        with tempfile.TemporaryDirectory() as tmp:
            o=Opener([error(429),good()]);c=self.client(tmp,o)
            c.complete('deepseek',[{'role':'user','content':'hello'}])
            self.assertEqual(o.requests[0],o.requests[1])
            records=[json.loads(p.read_text()) for p in c.records_dir.glob('*.json')]
            self.assertEqual(len(records),2)
            self.assertEqual(len({r['logical_request_id'] for r in records}),1)
            self.assertNotIn('secret-key-1234567890',json.dumps(records))
            self.assertAlmostEqual(c.budget.total_reserved(),sum(r['reserved_usd'] for r in records))
    def test_no_retry_for_payment_or_long_wait(self):
        for code,header in [(402,'0'),(401,'0'),(429,'60')]:
            with tempfile.TemporaryDirectory() as tmp:
                o=Opener([error(code,header)]);c=self.client(tmp,o)
                with self.assertRaises(g.GatewayError):c.complete('deepseek',[])
                self.assertEqual(len(o.requests),1)
    def test_retries_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            o=Opener([error(429)]*3);c=self.client(tmp,o)
            with self.assertRaises(g.GatewayError):c.complete('deepseek',[])
            self.assertEqual(len(o.requests),3)
    def test_serial_call_violation_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=good();value['choices'][0]['message']['tool_calls']=[{},{}]
            o=Opener([value]);c=self.client(tmp,o);c.serial_tools=True
            with self.assertRaises(g.GatewayError):c.complete('deepseek',[],tools=[{'type':'function'}])
            self.assertFalse(o.requests[0]['parallel_tool_calls'])
    def test_bad_retry_after_uses_backoff(self):
        self.assertEqual(g.retry_delay('nonsense',0),2)
        self.assertEqual(g.retry_delay('NaN',1),4)
        self.assertEqual(g.retry_delay('0',0),0)

if __name__=='__main__':unittest.main()
