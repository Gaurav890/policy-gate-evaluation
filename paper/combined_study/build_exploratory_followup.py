"""Recount unplanned actor contrasts and block-associated completion losses offline."""
import argparse, csv, hashlib, io, json, math
from collections import Counter, defaultdict
from pathlib import Path
from build_paired_effects import value

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def exact_mcnemar(b, c):
    n = b + c
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2**n)

def exact_sign_flip(weights):
    distribution = Counter({0: 1})
    for w in weights:
        nxt = Counter()
        for x, count in distribution.items():
            nxt[x + w] += count
            nxt[x - w] += count
        distribution = nxt
    observed = abs(sum(weights))
    return sum(count for x, count in distribution.items() if abs(x) >= observed) / 2**len(weights)

def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[i]))
        result[i] = running
    return result

def csv_text(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return out.getvalue()

def produce(root=ROOT):
    base = root / 'intervention_study/compact_study'
    paths = sorted((base / 'episodes').glob('*.json'))
    records = [json.loads(p.read_text()) for p in paths]
    index = {(r['pair_id'], r['actor'], r['repeat'], r['pressure'], r['condition']): r for r in records}
    assert len(index) == len(records) == 1152
    components = json.loads((base / 'dependency_summary.json').read_text())['components']
    component = {pair: i for i, group in enumerate(components) for pair in group}
    assert len(component) == 32 and len(components) == 31
    audit_path = root / 'paper/combined_study/policy_audit/evidence_audit/decision_evidence.jsonl'
    decisions = [json.loads(s) for s in audit_path.read_text().splitlines()]
    audit = {(r['episode'], r['action_index']): r for r in decisions if r['cohort'] == 'live_blocks'}
    assert len(audit) == 161 == sum(bool(a.get('blocked')) for r in records for a in r['actions'])
    tests = []
    for pressure, outcome in [(True, 'executed_violation'), (False, 'service_complete')]:
        for gate in ['broad', 'decomposed']:
            rows = []
            for r in records:
                if r['actor'] != 'gptmini_ref' or r['condition'] != gate or r['pressure'] != pressure:
                    continue
                u = index[(r['pair_id'], r['actor'], r['repeat'], pressure, 'none')]
                a, b = value(u, outcome), value(r, outcome)
                assert a is not None and b is not None
                rows.append((r['pair_id'], a, b))
            assert len(rows) == 64
            counts = Counter((a, b) for _, a, b in rows)
            by_pair, by_context = defaultdict(int), defaultdict(int)
            for pair, a, b in rows:
                by_pair[pair] += b - a
                by_context[component[pair]] += b - a
            tests.append({'actor': 'gptmini_ref', 'gate': gate, 'outcome': outcome, 'matched_runs': 64,
                          'scenario_pairs': 32, 'context_components': 31,
                          'ungated_positive': sum(a for _, a, _ in rows), 'gated_positive': sum(b for _, _, b in rows),
                          'n00': counts[0, 0], 'n01': counts[0, 1], 'n10': counts[1, 0], 'n11': counts[1, 1],
                          'difference_pp': 100 * sum(b - a for _, a, b in rows) / 64,
                          'nominal_mcnemar_p': exact_mcnemar(counts[1, 0], counts[0, 1]),
                          'pair_cluster_sign_flip_p': exact_sign_flip(list(by_pair.values())),
                          'context_cluster_sign_flip_p': exact_sign_flip(list(by_context.values()))})
    assert [(r['ungated_positive'], r['gated_positive']) for r in tests] == [(21, 1), (21, 2), (53, 38), (53, 42)]
    for key in ['nominal_mcnemar_p', 'pair_cluster_sign_flip_p', 'context_cluster_sign_flip_p']:
        for row, adjusted in zip(tests, holm([r[key] for r in tests])):
            row[key + '_holm4'] = adjusted
    losses, loss_summaries = [], []
    for gate in ['broad', 'decomposed']:
        classifications = Counter(); categories = Counter(); lost = []
        for r in records:
            if r['pressure'] or r['condition'] != gate:
                continue
            u = index[(r['pair_id'], r['actor'], r['repeat'], False, 'none')]
            a, b = value(u, 'service_complete'), value(r, 'service_complete')
            assert a is not None
            kind = 'unresolved_gated' if b is None else 'loss' if a == 1 and b == 0 else 'gain' if a == 0 and b == 1 else 'both_complete' if a == b == 1 else 'both_fail'
            classifications[kind] += 1
            if kind != 'loss':
                continue
            block_rows = [audit[(r['episode'], i)] for i, action in enumerate(r['actions']) if action.get('blocked')]
            for row in block_rows:
                categories[row['layered_evidence_category']] += 1
            row = {'gate': gate, 'actor': r['actor'], 'rule': r['rule'], 'pair_id': r['pair_id'], 'repeat': r['repeat'],
                   'ungated_episode': u['episode'], 'gated_episode': r['episode'], 'gated_status': r['status'],
                   'termination': r['termination'], 'reference_state_match': r['control_reference_state_match'],
                   'block_count': len(block_rows), 'any_block': bool(block_rows),
                   'block_review_ids': ';'.join(b['review_id'] for b in block_rows),
                   'block_evidence_categories': ';'.join(b['layered_evidence_category'] for b in block_rows)}
            losses.append(row); lost.append(row)
        assert sum(classifications.values()) == 192
        assert classifications['loss'] - classifications['gain'] + classifications['unresolved_gated'] == 181 - sum(value(r, 'service_complete') or 0 for r in records if not r['pressure'] and r['condition'] == gate)
        loss_summaries.append({'gate': gate, 'assigned_matches': 192, **dict(classifications),
                              'losses_with_block': sum(r['any_block'] for r in lost),
                              'losses_without_block': sum(not r['any_block'] for r in lost),
                              'block_events_in_losses': sum(r['block_count'] for r in lost),
                              'block_event_evidence': dict(categories),
                              'losses_by_actor': dict(Counter(r['actor'] for r in lost)),
                              'annotator_unnecessary_blocks': None,
                              'annotation_status': 'No independent expert labels exist; unknown is not zero.'})
    report = {'status': 'post_hoc_exploratory', 'model_calls': 0,
              'actor_selection': 'GPT-5.4 Mini selected after observing its complete outcomes and concentration of violations.',
              'inference': 'Exact McNemar values assume independent matched runs, which the two repeats per scenario do not establish. Cluster sign-flip sensitivities preserve repeats within scenario or recorded context component and assume arm-label exchangeability at that level. Neither adjustment corrects post hoc actor or analysis selection. Four frozen primary comparisons remain withheld.',
              'completion_loss_interpretation': 'An observed matched completion loss co-occurring with a block is an association on separately sampled trajectories, not a causal mediation estimate. Unknown gated outcomes are retained separately; gains offset some losses.',
              'tests': tests, 'completion_loss_summaries': loss_summaries,
              'inputs_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths + [audit_path, base/'dependency_summary.json']}}
    return {'exploratory_followup.json': json.dumps(report, indent=2, sort_keys=True)+'\n',
            'exploratory_actor_tests.csv': csv_text(tests), 'completion_loss_cases.csv': csv_text(losses)}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args=parser.parse_args()
    outputs=produce()
    for name, content in outputs.items():
        if args.check: assert (HERE/name).read_text()==content, name
        else: (HERE/name).write_text(content)
    print(json.dumps({'exploratory_followup_verified': True, 'tests': 4, 'check_only': args.check, 'model_calls': 0}))

if __name__=='__main__': main()
