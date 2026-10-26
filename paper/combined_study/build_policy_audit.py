"""Export policy evidence inputs from saved records; never run inference."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from build_results import build

ROOT = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_id(prefix, value):
    return prefix + hashlib.sha256(('policy-review-v1:' + digest(value)).encode()).hexdigest()[:16]


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n'


def json_lines(values):
    return ''.join(json.dumps(v, ensure_ascii=False, sort_keys=True) + '\n' for v in values)


def produce():
    tables, _ = build(ROOT)
    base = ROOT / 'intervention_study/compact_study'
    native = {r['episode']: r for r in json.loads((base / 'native_verification.json').read_text())['records']}
    proposals, source_map, policies = {}, {}, {}
    source_hashes, shadow_count, live_count, checked_inputs = {}, 0, 0, 0

    def remember(path):
        rel = str(path.relative_to(ROOT))
        source_hashes[rel] = sha(path)
        return rel

    def add(public, source):
        rid = review_id('P-', public)
        record = {'review_id': rid, 'public_input': public}
        if rid in proposals:
            assert proposals[rid] == record, 'Review ID collision'
        proposals[rid] = record
        source_map.setdefault(rid, []).append(source)
        return rid

    for path in sorted((base / 'shadow').glob('*.json')):
        source = remember(path)
        saved = json.loads(path.read_text())
        for row in saved['rows']:
            public = row['public']
            assert digest(public) == row['public_sha256']
            domain = row['rule'].split('_')[0]
            template = {k: public[k] for k in ['policy', 'tools']}
            if domain in policies:
                assert policies[domain] == template
            policies[domain] = template
            add(public, {'cohort': 'all_ungated_shadow_proposals', 'source': source,
                'episode': row['episode'], 'proposal_id': row['proposal_id'],
                'action_index': row['action_index'], 'public_input_sha256': row['public_sha256']})
            shadow_count += 1
    assert set(policies) == {'airline', 'retail'}

    conversations, conversation_key = {}, {}
    live_conditions = Counter()
    for path in sorted((base / 'episodes').glob('*.json')):
        record = json.loads(path.read_text())
        source = remember(path)
        for index, action in enumerate(record['actions']):
            if not action['blocked']:
                continue
            assert action['mutates']
            public = {**policies[record['rule'].split('_')[0]],
                'conversation_prefix': record['canonical_messages'][:action['message_index'] + 1 + action['call_index']],
                'current_write': action['call']}
            for check in action['gate'].get('checks', []):
                if 'request_record' in check:
                    assert check['public_input_sha256'] == digest(public)
                    checked_inputs += 1
            native_block = next(b for b in native[record['episode']]['blocks'] if b['action_index'] == index)
            add(public, {'cohort': 'all_live_blocks', 'source': source, 'episode': record['episode'],
                'action_index': index, 'condition': record['condition'],
                'public_input_sha256': digest(public), 'native_replay': native_block})
            live_count += 1
            live_conditions[record['condition']] += 1
        if not record['pressure']:
            public = {**policies[record['rule'].split('_')[0]], 'conversation': record['canonical_messages']}
            # Full trajectories stay separate even when their visible text is identical.
            rid = review_id('C-', record['episode'])
            assert rid not in conversations
            conversations[rid] = {'review_id': rid, 'public_record': public}
            conversation_key[rid] = {'source': source, 'episode': record['episode'],
                'actor': record['actor'], 'condition': record['condition'],
                'pair_id': record['pair_id'], 'rule': record['rule'],
                'record_status': record['status'], 'termination': record['termination'],
                'frozen_reference_state_match': record.get('control_reference_state_match'),
                'proposal_review_ids': sorted(rid for rid, sources in source_map.items()
                    if any(s['episode'] == record['episode'] for s in sources))}
    assert shadow_count == 231 and live_count == 161
    assert live_conditions == {'broad': 102, 'decomposed': 59}
    assert len(conversations) == 576
    assert sum(len(v) for v in source_map.values()) == shadow_count + live_count
    assert all(set(p) == {'review_id', 'public_input'} for p in proposals.values())
    assert all(set(p['public_input']) == {'policy', 'tools', 'conversation_prefix', 'current_write'} for p in proposals.values())
    assert all(set(p['public_record']) == {'policy', 'tools', 'conversation'} for p in conversations.values())

    outputs = {
        'proposal_cases.jsonl': json_lines([proposals[k] for k in sorted(proposals)]),
        'conversation_cases.jsonl': json_lines([conversations[k] for k in sorted(conversations)]),
        'coordinator_key.json': json_text({'scope': 'Provenance mappings and frozen measurements for the programmatic evidence audit.',
            'proposal_sources': source_map, 'conversation_sources': conversation_key,
            'source_file_sha256': source_hashes})}
    manifest = {
        'status': 'evidence_inputs_exported',
        'scope': 'Inputs to a post hoc programmatic policy-evidence audit, separate from frozen outcomes and inference.',
        'selection': 'Every ungated shadow write and every live blocked write, plus all nominally permitted live conversations.',
        'shadow_proposal_events': shadow_count, 'live_block_events': live_count,
        'live_blocks_by_condition': dict(live_conditions), 'unique_public_proposals': len(proposals),
        'nominally_permitted_conversations': len(conversations),
        'live_model_check_inputs_hash_verified': checked_inputs,
        'processing_manifest_sha256': sha(base / 'completion/processing_manifest.json'),
        'frozen_live_records': tables['collection']['live_assigned'],
        'public_input_files': ['proposal_cases.jsonl', 'conversation_cases.jsonl', 'README.md'],
        'provenance_files': ['coordinator_key.json', 'manifest.json'],
        'masking_limit': 'Actor and gate metadata, current gate decisions, private predicates, and frozen endpoint scores are omitted from public-input records. Prior gate feedback in live public transcripts is preserved and can reveal treatment; this is not complete blinding.',
        'outputs_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in outputs.items()},
        'network_calls': 0, 'model_calls': 0}
    outputs['manifest.json'] = json_text(manifest)
    return outputs, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='Create missing exports; refuse to overwrite different contents.')
    parser.add_argument('--check', action='store_true', help='Verify exact exports without writing (default).')
    args = parser.parse_args()
    assert not (args.write and args.check)
    outputs, manifest = produce()
    dest = Path(__file__).resolve().parent / 'policy_audit'
    if args.write:
        dest.mkdir(exist_ok=True)
    for name, content in outputs.items():
        path = dest / name
        if path.exists():
            assert path.read_text() == content, 'Export differs; preserve and investigate: ' + name
        elif args.write:
            path.write_text(content)
        else:
            raise AssertionError('Missing export: ' + name)
    print(json.dumps({k: manifest[k] for k in ['status', 'shadow_proposal_events',
        'live_block_events', 'unique_public_proposals', 'nominally_permitted_conversations', 'network_calls', 'model_calls']}))


if __name__ == '__main__':
    main()
