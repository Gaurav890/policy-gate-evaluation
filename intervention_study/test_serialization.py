"""Nested tool-return conversion including a real flight-search result."""
import json,unittest
from pydantic import BaseModel
from intervention_study.common import ROOT,read,environment,BASE
from intervention_study.serialization import to_json
class SerializationTests(unittest.TestCase):
    def test_nested_model_values(self):
        class Item(BaseModel):number:int
        original={'items':[Item(number=4)],'tuple':(Item(number=5),)}
        self.assertEqual(json.loads(json.dumps(to_json(original))),{'items':[{'number':4}],'tuple':[{'number':5}]})
        self.assertIsInstance(original['items'][0],Item)
    def test_real_interrupted_search_output(self):
        case=next(c for c in read(BASE/'cases.json') if c['case_id']=='airline_basic_economy-00-control')
        ledger=ROOT/'groundwork/spend_ledger.jsonl'
        rows=[json.loads(x) for x in ledger.read_text().splitlines() if 'intervention-breadth-airline_basic_economy-00-control--deepseek_ref--none--0' in x] if ledger.exists() else []
        if not rows:
            from intervention_study.evidence import archive
            rows=[r for r in archive().values() if r.get('episode')=='intervention-breadth-airline_basic_economy-00-control--deepseek_ref--none--0']
        call=None
        for row in rows:
            from intervention_study.evidence import receipt
            rec=receipt(row['request_id'])
            for choice in rec.get('response',{}).get('choices',[]):
                for c in choice.get('message',{}).get('tool_calls',[]):
                    if c['function']['name']=='search_direct_flight':call=c['function']
        self.assertIsNotNone(call)
        env=environment(case);before=env.get_db_hash();result=env.make_tool_call(call['name'],**json.loads(call['arguments']))
        self.assertIsInstance(result,list);json.dumps(to_json(result));self.assertEqual(before,env.get_db_hash())
if __name__=='__main__':unittest.main()
