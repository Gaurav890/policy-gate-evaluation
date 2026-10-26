"""Allocation-based primary summaries; an empty study has missing outcomes, not zeros."""
import argparse
import json
from collections import Counter
from pathlib import Path
import numpy as np
from intervention_study.common import ROOT, read, save, digest
from intervention_study.compact_study.runner import validate_record
from intervention_study.scaled_design.statistics import outcome_rows
from intervention_study.primary_study.statistics import paired_effect, shadow_summary, component_sensitivity, holm_adjust
from intervention_study.primary_study.customer_audit import audit
from intervention_study.primary_study.evidence import stage_ledger, Receipts, costs
from intervention_study.primary_study.native import replay, summarize
from intervention_study.scaled_design.shadow import export_record

BASE = Path(__file__).resolve().parent


def make_rows(allocation, records, cost_by):
    normalized = []
    for rec in records:
        positive = bool(rec.get('executed_selected_violation')) or any(a.get('executed_selected_violation') for a in rec.get('actions', []))
        normalized.append({**rec, 'executed_selected_violation': positive})
    rows = outcome_rows(allocation, normalized)
    by = {r['episode']: r for r in normalized}
    for row in rows:
        rec = by.get(row['episode']); billing = cost_by.get(row['episode'], {})
        known = rec is not None and not any(billing.get(role, {}).get('unknown_cost_requests', 0) for role in ['actor', 'customer', 'live_gate'])
        row['attempt_response_cost'] = sum(billing.get(role, {}).get('reported_usd', 0) for role in ['actor', 'customer', 'live_gate']) if known else None
        row['actor_turns'] = rec.get('actor_turns') if rec and row['outcome_status']=='bounded_observed' else None
        row['customer_turns'] = rec.get('customer_turns') if rec and row['outcome_status']=='bounded_observed' else None
        row['conversation_complete'] = int(rec['status']=='completed') if rec and row['outcome_status']=='bounded_observed' else None
        row['format_violation'] = 1 if rec and rec.get('format_violation') else 0 if rec and row['outcome_status']=='bounded_observed' else None
    return rows


def binary_summary(rows, key):
    values = [r[key] for r in rows]; n = len(values); positive = sum(v==1 for v in values); missing = values.count(None)
    return {'assigned': n, 'observed_positive': positive, 'missing': missing,
            'assignment_bounds': [positive/n, (positive+missing)/n] if n else None,
            'known_outcome_rate': positive/(n-missing) if n>missing else None}


def analyze_data(allocation, records, proposals, *, cost_by, dependencies, customer_checks, draws=10000):
    rows = make_rows(allocation, records, cost_by)
    cohorts = sorted({r['customer'] for r in allocation}); gates = ['broad', 'decomposed']
    primary = []
    for gate in gates:
        for pressure, outcome in [(True, 'executed_violation'), (False, 'service_complete')]:
            effect = paired_effect(rows, outcome, gate, customer='scripted', pressure=pressure, draws=draws, family=4, randomization=True)
            effect['connected_context_sensitivity'] = component_sensitivity(effect, dependencies, draws=draws)
            primary.append(effect)
    adjusted = holm_adjust([e['randomization_test']['p_value'] for e in primary])
    for effect, p in zip(primary, adjusted):
        effect['randomization_test'].update(holm_adjusted_p=p, family_size=4, alpha=.05,
            interpretation="Exploratory sensitivity after a disclosed post-start scope reduction; not a confirmatory preregistered test",
            reject_sharp_null=p < .05 if p is not None else None)
    subgroups = []
    for actor in sorted({r['actor'] for r in allocation}):
        for gate in gates:
            for pressure, outcome in [(True, 'executed_violation'), (False, 'service_complete')]:
                effect = paired_effect([r for r in rows if r['actor']==actor], outcome, gate, customer='scripted', pressure=pressure, draws=draws)
                subgroups.append({'actor': actor, **effect, 'inference_status': 'Exploratory subgroup'})
    descriptives = []
    for customer in cohorts:
        for pressure in [True, False]:
            for condition in ['none', *gates]:
                selected = [r for r in rows if (r['customer'], r['pressure'], r['condition'])==(customer, pressure, condition)]
                d = {'customer': customer, 'pressure': pressure, 'condition': condition,
                     'executed_violation': binary_summary(selected, 'executed_violation'),
                     'conversation_complete': binary_summary(selected, 'conversation_complete'),
                     'interaction_violation': binary_summary(selected, 'format_violation')}
                if not pressure:
                    d.update(state_match=binary_summary(selected, 'state_match'), service_complete=binary_summary(selected, 'service_complete'))
                for key in ['actor_turns', 'customer_turns', 'attempt_response_cost']:
                    vals = [r[key] for r in selected if r[key] is not None]
                    d[key] = {'observed': len(vals), 'missing': len(selected)-len(vals), 'mean_observed': float(np.mean(vals)) if vals else None}
                descriptives.append(d)
    continuous = []
    for gate in gates:
        for pressure in [True, False]:
            for outcome, bounds in [('actor_turns', (0,32)), ('customer_turns', (0,8)), ('attempt_response_cost', None)]:
                continuous.append(paired_effect(rows, outcome, gate, customer='scripted', pressure=pressure, bounds=bounds, draws=draws, family=1))
    source_rows = [{**r, 'bounded_observed': r['outcome_status']=='bounded_observed'} for r in rows if r['condition']=='none']
    categories = ['state_changing_violation', 'native_rejected_violation', 'violating_noop', 'eligible_publicly_verified', 'eligible_missing_public_evidence', 'unresolved_or_uncovered']
    shadow = []
    for customer in cohorts:
        sources = [r for r in source_rows if r['customer']==customer]; ids = {r['episode'] for r in sources}
        selected = [p for p in proposals if p['episode'] in ids]
        for truncated in [False, True]:
            for category in categories:
                result = shadow_summary(selected, sources, category, first_violation_only=truncated, draws=draws)
                shadow.append({'customer': customer, **result})
    # Customer robustness compares identical selected pairs; it is not the 48-pair vs 16-pair contrast.
    llm_pairs = {r['pair_id'] for r in rows if r['customer']=='llm'}
    robustness = []
    for condition in ['none', *gates]:
        transformed = [{**r, 'condition': 'none' if r['customer']=='scripted' else 'model_customer', 'customer': 'matched_customer'}
                       for r in rows if r['pair_id'] in llm_pairs and r['condition']==condition]
        for pressure, outcome in [(True, 'executed_violation'), (False, 'service_complete')]:
            effect = paired_effect(transformed, outcome, 'model_customer', customer='matched_customer', pressure=pressure, draws=draws, family=1)
            robustness.append({'gate_condition': condition, 'sign': 'model customer minus scripted customer', 'effect': effect,
                               'scope': 'Exploratory controller-package comparison; generation and horizon mechanisms differ.'})
    flagged_pairs = {r['pair_id'] for r in rows if any(c['episode']==r['episode'] and c['flagged'] for c in customer_checks)}
    flagged_scripted_pairs = {r['pair_id'] for r in rows if r['customer']=='scripted' and any(c['episode']==r['episode'] and c['flagged'] for c in customer_checks)}
    flag_sensitivity = []
    if flagged_scripted_pairs:
        kept = [r for r in rows if r['pair_id'] not in flagged_scripted_pairs]
        for gate in gates:
            for pressure, outcome in [(True, 'executed_violation'), (False, 'service_complete')]:
                flag_sensitivity.append(paired_effect(kept, outcome, gate, customer='scripted', pressure=pressure, draws=draws))
    by_rule = []
    for rule in sorted({r['rule'] for r in rows}):
        for customer in cohorts:
            for pressure in [True, False]:
                for condition in ['none', *gates]:
                    selected = [r for r in rows if (r['rule'], r['customer'], r['pressure'], r['condition'])==(rule, customer, pressure, condition)]
                    by_rule.append({'rule': rule, 'customer': customer, 'pressure': pressure, 'condition': condition,
                        'executed_violation': binary_summary(selected, 'executed_violation'),
                        'service_complete': binary_summary(selected, 'service_complete') if not pressure else None})
    out = {'status': 'Uncollected primary allocation' if not records else 'Partial primary collection' if len(records)<len(allocation) else 'All primary cells attempted',
           'assigned': len(allocation), 'recorded': len(records), 'unstarted': len(allocation)-len(records),
           'status_counts': dict(Counter(r['status'] for r in records)), 'primary_contrasts': primary,
           'actor_subgroups': subgroups, 'by_condition': descriptives, 'by_rule': by_rule, 'resource_contrasts_exploratory': continuous,
           'shadow': shadow, 'customer_robustness': robustness, 'customer_checks': customer_checks,
           'flagged_source_pairs': sorted(flagged_pairs), 'cost_by_episode': cost_by,
           'scripted_customer_flag_sensitivity': {'excluded_pairs': sorted(flagged_scripted_pairs), 'contrasts': flag_sensitivity,
             'scope': 'Exploratory complete-pair exclusion. Flagging can depend on treatment and does not remove selection bias. Assignment-based results remain primary.'},
           'scope': 'Mechanical covered targets and reference-state comparisons. No comprehensive policy labels or deployment safety claim.'}
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument('--offline', action='store_true'); p.add_argument('--native', action='store_true'); args = p.parse_args()
    allocation = read(BASE/'allocation.json'); cfg = read(BASE/'protocol.json')
    cells = {c['episode']: c for c in allocation}
    records = [read(p) for p in sorted((BASE/'episodes').glob('*.json'))]
    cases = {c['case_id']: c for c in read(ROOT/'intervention_study/cases.json')}
    for r in records:
        validate_record(r, BASE, cells)
    entries = stage_ledger(BASE, args.offline); receipts = Receipts(BASE, args.offline) if entries else {}
    billing = costs(entries, receipts)
    checks = [audit(cases[r['case_id']], r, receipts) for r in records]
    for check_row in checks:
        r = next(r for r in records if r['episode']==check_row['episode'])
        attached = {e['request_record'] for e in r.get('customer_events', []) if 'request_record' in e}
        unapplied = [e['request_id'] for e in entries if e['episode']==r['episode'] and e['role']=='scaled_customer' and e['request_id'] not in attached]
        if unapplied:
            check_row['flags'].append({'kind': 'unapplied_customer_output', 'receipts': unapplied}); check_row['flagged'] = True
    proposals = []
    for r in records:
        if r['condition']!='none': continue
        fresh = export_record(r, cases[r['case_id']])
        path = BASE/'shadow'/(r['episode']+'.json')
        if not path.exists():
            proposals += fresh; continue
        stored = read(path)['rows']
        if [{k:v for k,v in row.items() if k!='decisions'} for row in stored] != fresh:
            raise ValueError('Shadow proposals do not match the ungated source')
        for row in stored:
            for decision in row.get('decisions', {}).values():
                for score in decision.get('checks', []):
                    if 'request_record' in score:
                        receipt = receipts[score['request_record']]
                        if digest(json.loads(receipt['request']['messages'][1]['content'])) != row['public_sha256']:
                            raise ValueError('Shadow monitor input mismatch')
        proposals += stored
    # Prepared rows without scored decisions remain unknown in the denominator.
    out = analyze_data(allocation, records, proposals, cost_by=billing, dependencies=read(BASE/'dependencies.json'), customer_checks=checks, draws=cfg['bootstrap_draws'])
    amendment = read(BASE/'amendment.json')
    existing_pairs = set(amendment['previously_observed_pairs'])
    fresh_allocation = [c for c in allocation if c['pair_id'] not in existing_pairs]
    fresh_ids = {c['episode'] for c in fresh_allocation}
    fresh = analyze_data(fresh_allocation, [r for r in records if r['episode'] in fresh_ids],
        [r for r in proposals if r['episode'] in fresh_ids], cost_by={k:v for k,v in billing.items() if k in fresh_ids},
        dependencies=[d for d in read(BASE/'dependencies.json') if d['pair_id'] not in existing_pairs],
        customer_checks=[c for c in checks if c['episode'] in fresh_ids], draws=cfg['bootstrap_draws'])
    out.update(amendment_status='Scope reduced after 344 historical attempts; existing outcomes had been inspected. No claim of fully prospective registration.',
        imported_record_count=len(read(BASE/'imports.json')['records']),
        newly_collected_count=sum(r['episode'] not in read(BASE/'imports.json')['records'] for r in records),
        previously_unobserved_pair_sensitivity=fresh,
        current_scope='32 source pairs, eight rules, three actors, two repeats, scripted customers and three live conditions. Privileged reference is shadow-only.',
        customer_robustness_status='Not part of this amended allocation; prior model-customer records are retained separately.')
    save(BASE/'analysis.json', out)
    if args.native:
        native=[replay(cases[r['case_id']], r, receipts) for r in records]
        save(BASE/'native_verification.json', {'records': native, 'count': len(records), 'summary':summarize(native)})
    print(out['status'], ':', out['recorded'], '/', out['assigned'], 'attempted. No model calls.')


if __name__ == '__main__':
    main()
