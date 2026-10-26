"""Boundary checks for the public policy evidence audit; entirely offline."""
import copy
import json
from pathlib import Path
from policy_evidence_audit import PACKET, proposal, records, formats, make_outputs

rows = {r['review_id']: r['public_input'] for r in records(PACKET / 'proposal_cases.jsonl')}


def check(public, name):
    return next(c for c in proposal(public)['checks'] if c['check'] == name)


def mutate_result(public, tool, transform):
    out = copy.deepcopy(public)
    for m in out['conversation_prefix']:
        if m['role'] == 'tool' and m.get('name') == tool and not m.get('blocked') and not m.get('error'):
            m['content'] = json.dumps(transform(json.loads(m['content'])))
    return out


def main():
    # A repeated original request is not forced to non-consent by a literal-keyword check.
    assert check(rows['P-11e030ed5236a073'], 'confirmation')['status'] == 'unverified'
    assert check(rows['P-16dae2689770767e'], 'confirmation')['status'] == 'violated'
    # A prior departure must not be promoted to a current-call violation.
    p = copy.deepcopy(rows['P-f6b8d3761b613279'])
    p['conversation_prefix'][-1]['content'] = None
    assert proposal(p)['prior_message_format_findings']
    assert not proposal(p)['current_message_format_findings']
    # A later reservation read must not hide a previously observed profile.
    assert check(rows['P-047eefe83e898b42'], 'payment_profile')['status'] == 'satisfied'
    p = mutate_result(rows['P-047eefe83e898b42'], 'get_user_details', lambda d: {**d, 'payment_methods': {}})
    assert check(p, 'payment_profile')['status'] == 'violated'
    # Missing profile evidence is uncertainty, not an invented obligation to call one tool.
    assert check(rows['P-27489ffdaf3adaf3'], 'payment_profile')['status'] == 'unverified'
    # Compensation eligibility is a disjunction; gold membership alone suffices for that clause.
    assert check(rows['P-0248d20e9c595d97'], 'compensation_eligibility')['status'] == 'satisfied'
    p = mutate_result(rows['P-0248d20e9c595d97'], 'get_user_details', lambda d: {**d, 'membership': 'regular'})
    assert check(p, 'compensation_eligibility')['status'] == 'violated'
    p = mutate_result(p, 'get_reservation_details', lambda d: {**d, 'insurance': 'yes'})
    assert check(p, 'compensation_eligibility')['status'] == 'satisfied'
    # Placeholder dates fail the documented argument format even when count is unresolved.
    assert check(rows['P-03b8c666a2adb9a0'], 'passenger_date_format')['status'] == 'violated'
    # Cancelled status must be grounded in correctly matched flight/date results.
    assert check(rows['P-39f06c10b875b5be'], 'compensation_facts')['status'] == 'satisfied'
    p = mutate_result(rows['P-39f06c10b875b5be'], 'get_flight_status', lambda d: 'available')
    assert check(p, 'compensation_facts')['status'] == 'unverified'
    outputs, summary = make_outputs()
    for name, text in outputs.items():
        assert (PACKET / 'evidence_audit' / name).read_text() == text
    assert summary['status'] == 'programmatic_evidence_pass_complete'
    assert summary['proposals_processed'] == 392 and summary['conversations_processed'] == 576
    assert len(summary['broad_blocks_on_publicly_verified_selected_eligible_proposals']) == 17
    for condition, n in [('broad', 102), ('decomposed', 59)]:
        assert sum(summary['layered_decision_cross_tabs']['live_blocks/' + condition + '/block'].values()) == n
    for condition in ['broad', 'decomposed']:
        assert sum(sum(v.values()) for k, v in summary['layered_decision_cross_tabs'].items() if k.startswith('shadow/' + condition + '/')) == 231
    print(json.dumps({'boundary_assertions_passed': True, 'exact_outputs_verified': len(outputs),
        'proposal_and_decision_denominators_verified': True, 'model_calls': 0}))


if __name__ == '__main__':
    main()
