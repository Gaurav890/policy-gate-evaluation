"""Shared paths, public transcript conversion, and immutable study manifests."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'intervention_study'
sys.path.insert(0, str(ROOT))
RULES = ['airline_cancellation', 'airline_basic_economy', 'airline_passenger_count',
         'airline_compensation', 'retail_return_status', 'retail_refund_destination',
         'retail_identity_lookup', 'retail_post_item_change']

def read(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)

def digest(value):
    if isinstance(value, Path):
        return hashlib.sha256(value.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def serial(value):
    return value.model_dump(mode='json') if hasattr(value, 'model_dump') else value

def canonical(message):
    out = {'role': message['role'], 'content': message.get('content')}
    if message.get('tool_calls'):
        out['tool_calls'] = [{'id': c['id'], 'name': c['function']['name'],
                             'arguments': json.loads(c['function']['arguments'])}
                            for c in message['tool_calls']]
    if message.get('role') == 'tool':
        out.update(tool_call_id=message['tool_call_id'], name=message.get('name'),
                   error=message.get('error', False), blocked=message.get('blocked', False))
    return out

def environment(case):
    from benchmark_adapter import CONSTRUCTORS
    from tau2.domains.airline.data_model import FlightDB
    from tau2.domains.retail.data_model import RetailDB
    env = CONSTRUCTORS[case['domain']]()
    raw = env.tools.db.model_dump(mode='json')
    for table, rows in case['overrides'].items():
        raw[table].update(rows)
    cls = FlightDB if case['domain'] == 'airline' else RetailDB
    return CONSTRUCTORS[case['domain']](db=cls.model_validate(raw))

def verify_freeze():
    for rel, expected in read(BASE / 'freeze.json')['files'].items():
        assert digest(ROOT / rel) == expected, 'Frozen source changed: ' + rel
    return read(BASE / 'protocol.json')
