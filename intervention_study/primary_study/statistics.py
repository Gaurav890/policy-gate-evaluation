"""Paired source-pair inference for fixed rule strata and shared proposals."""
from collections import defaultdict
import numpy as np


def paired_randomization(differences, rules, *, draws=10000, seed=20261012):
    """Two-sided paired label swaps; sharp-null validity needs assignment exchangeability."""
    d = np.asarray(differences, dtype=float)
    if not len(d) or len(d) != len(rules) or not np.all(np.isfinite(d)):
        return {'p_value': None, 'reason': 'No complete paired allocation'}
    coefficients = np.array([1/(len(set(rules))*rules.count(r)) for r in rules])
    weighted = d*coefficients
    observed = float(weighted.sum())
    exact = len(d) <= 16
    if exact:
        codes = np.arange(2**len(d), dtype=np.uint32)[:, None]
        signs = 2*((codes >> np.arange(len(d))) & 1).astype(float)-1
    else:
        signs = 2*np.random.default_rng(seed).integers(0, 2, size=(draws, len(d)))-1
    distribution = signs @ weighted
    exceed = int(np.sum(np.abs(distribution) >= abs(observed)-1e-12))
    p = exceed/len(distribution) if exact else (exceed+1)/(len(distribution)+1)
    return {'p_value': float(p), 'statistic': observed, 'two_sided': True,
            'permutations': len(distribution), 'exact_enumeration': exact,
            'null': 'Sharp no-effect null, conditional on randomized condition positions within blocks.',
            'assumptions': 'Joint source-pair label swaps preserve the assignment mechanism; stable potential outcomes and no inter-run interference. Not a test of every weak mean-null or a population guarantee.'}


def holm_adjust(p_values):
    """Missing tests retain their place in the full prespecified family."""
    vals = np.array([1.0 if p is None else p for p in p_values])
    if np.any((vals < 0) | (vals > 1)) or not np.all(np.isfinite(vals)):
        raise ValueError('Invalid p value')
    order = np.argsort(vals, kind='stable')
    adjusted = np.empty(len(vals))
    adjusted[order] = np.minimum(1, np.maximum.accumulate(vals[order]*(len(vals)-np.arange(len(vals)))))
    return [None if p is None else float(a) for p, a in zip(p_values, adjusted)]


def _interval(samples, family=1):
    good = np.asarray([x for x in samples if np.isfinite(x)], dtype=float)
    if not len(good):
        return {'ci95': None, 'nominal_expanded_interval': None, 'undefined_draws': len(samples), 'degenerate': False}
    return {'ci95': np.quantile(good, [.025, .975]).tolist(),
            'nominal_expanded_interval': np.quantile(good, [.025/family, 1-.025/family]).tolist(),
            'undefined_draws': len(samples)-len(good), 'degenerate': bool(np.ptp(good) == 0)}


def bootstrap_weights(pair_rules, draws=10000, seed=20261012):
    """One draw preserves every observation belonging to the sampled pair."""
    rng = np.random.default_rng(seed)
    weights = np.zeros((draws, len(pair_rules)), dtype=np.int16)
    for rule in sorted(set(pair_rules)):
        columns = [i for i, r in enumerate(pair_rules) if r == rule]
        counts = rng.multinomial(len(columns), [1/len(columns)]*len(columns), size=draws)
        weights[:, columns] = counts
    return weights


def _macro(values, rules):
    return float(np.mean([np.mean([v for v, r in zip(values, rules) if r == rule]) for rule in sorted(set(rules))])) if rules else None


def paired_effect(rows, outcome, gate, *, customer, pressure, draws=10000, seed=20261012, bounds=(0, 1), family=6, randomization=False):
    selected = [r for r in rows if r['customer'] == customer and r['pressure'] == pressure and r['condition'] in ['none', gate]]
    keyed = {}
    for row in selected:
        key = (row['pair_id'], row['actor'], row['repeat'], row['condition'])
        if key in keyed:
            raise ValueError('Duplicate cell')
        value = row[outcome]
        if value is not None and (not np.isfinite(value) or bounds is not None and not bounds[0] <= value <= bounds[1]):
            raise ValueError('Invalid outcome')
        keyed[key] = row
    pairs = sorted({r['pair_id'] for r in selected})
    deltas, rules, limits, missing = [], [], [], []
    for pair in pairs:
        arms = [{k[1:3]: r for k, r in keyed.items() if k[0] == pair and k[-1] == arm} for arm in ['none', gate]]
        if not arms[0] or arms[0].keys() != arms[1].keys():
            raise ValueError('Unpaired allocation; missing cells must be explicit')
        pair_rules = {r['rule'] for arm in arms for r in arm.values()}
        if len(pair_rules) != 1:
            raise ValueError('Inconsistent rule for pair')
        rules.append(next(iter(pair_rules)))
        values = [[r[outcome] for r in arm.values()] for arm in arms]
        if any(v is None for a in values for v in a):
            deltas.append(np.nan); missing.append(pair)
        else:
            deltas.append(float(np.mean(values[1])-np.mean(values[0])))
        if bounds is not None:
            lo, hi = bounds
            arm_bounds = [(np.mean([lo if v is None else v for v in a]), np.mean([hi if v is None else v for v in a])) for a in values]
            limits.append((arm_bounds[1][0]-arm_bounds[0][1], arm_bounds[1][1]-arm_bounds[0][0]))
    out = {'gate': gate, 'outcome': outcome, 'customer': customer, 'pressure': pressure,
           'sign': 'gate minus no gate', 'assigned_pairs': len(pairs), 'missing_pairs': missing,
           'pair_differences': {p: None if not np.isfinite(d) else d for p, d in zip(pairs, deltas)},
           'assignment_bounds': [_macro([v[i] for v in limits], rules) for i in (0, 1)] if limits else None,
           'estimate': None, 'ci95': None, 'nominal_expanded_interval': None,
           'randomization_test': {'p_value': None},
           'interval_status': 'Descriptive percentile bootstrap only. Nominal coverage failed prospective calibration; intervals are not formal acceptance/rejection criteria.',
           'scope': 'Fixed rule templates; paired empirical bootstrap, not guaranteed population coverage.'}
    if not pairs or missing:
        out['warning'] = 'Assignment bounds retained; inferential intervals withheld for missing pair blocks.'
        return out
    weights = bootstrap_weights(rules, draws, seed)
    samples = np.mean([(weights[:, np.array(rules) == r] @ np.asarray(deltas)[np.array(rules) == r]) / rules.count(r) for r in sorted(set(rules))], axis=0)
    out.update(estimate=_macro(deltas, rules), **_interval(samples, family))
    if randomization:
        out['randomization_test'] = paired_randomization(deltas, rules, draws=draws, seed=seed+17)
    out.update(draws=draws, min_pairs_per_rule=min(rules.count(r) for r in set(rules)),
               warning='Degenerate empirical intervals do not establish zero population uncertainty.' if out['degenerate'] else None,
               leave_one_rule_out={r: _macro([d for d, rule in zip(deltas, rules) if rule != r], [rule for rule in rules if rule != r]) for r in sorted(set(rules))})
    return out


def shadow_class(row):
    private = row['private_oracle_checks']
    if row['covered_violation']:
        return 'state_changing_violation' if row['native_state_change'] else 'native_rejected_violation' if row['native_error'] else 'violating_noop'
    if private and all(x['verdict'] == 'clean' for x in private):
        public = row['public_predicate_checks']
        return 'eligible_publicly_verified' if public and all(x['verdict'] == 'clean' for x in public) else 'eligible_missing_public_evidence'
    return 'unresolved_or_uncovered'


def shadow_summary(proposals, sources, category, *, draws=10000, seed=20261012, first_violation_only=False):
    """Pooled-proposal rates with source-pair resampling, plus paired gate differences."""
    ids = [r['proposal_id'] for r in proposals]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate proposal')
    source_by = {s['episode']: s for s in sources}
    if len(source_by) != len(sources):
        raise ValueError('Duplicate source conversation')
    if any(r['episode'] not in source_by for r in proposals):
        raise ValueError('Proposal outside source allocation')
    pair_rules = {s['pair_id']: s['rule'] for s in sources}
    pairs = sorted(pair_rules); rules = [pair_rules[p] for p in pairs]
    index = {p: i for i, p in enumerate(pairs)}
    den = np.zeros(len(pairs)); counts = {g: np.zeros(len(pairs)) for g in ['broad', 'decomposed', 'oracle']}
    unknown = {g: np.zeros(len(pairs)) for g in counts}
    episode_counts = {s['episode']: 0 for s in sources}
    episode_blocks = {g: set() for g in counts}
    for row in proposals:
        if row['pair_id'] != source_by[row['episode']]['pair_id'] or row['rule'] != source_by[row['episode']]['rule']:
            raise ValueError('Proposal source mismatch')
        if first_violation_only and row['after_prior_executed_violation']:
            continue
        if shadow_class(row) != category:
            continue
        i = index[row['pair_id']]; den[i] += 1; episode_counts[row['episode']] += 1
        for gate in counts:
            d = row.get('decisions', {}).get(gate, {})
            missing = type(d.get('block')) is not bool or d.get('monitor_failure', False)
            unknown[gate][i] += missing
            if not missing and d['block']:
                counts[gate][i] += 1; episode_blocks[gate].add(row['episode'])
    incomplete = [s['episode'] for s in sources if not s['bounded_observed']]
    weights = bootstrap_weights(rules, draws, seed) if pairs else np.zeros((draws, 0))
    boot_den = weights @ den
    n = int(den.sum()); supported = den > 0
    out = {'category': category, 'first_violation_only': first_violation_only, 'proposals': n,
           'source_conversations': len(sources), 'source_pairs': len(pairs), 'pairs_with_denominator': int(supported.sum()),
           'source_conversations_with_denominator': sum(x > 0 for x in episode_counts.values()),
           'incomplete_sources': incomplete, 'weighting': 'Pooled proposals primary; equal supported-pair mean sensitivity.',
           'scope': 'Conditional on observed ungated proposals. Unseen proposals after interruptions have no identified denominator.',
           'gates': {}, 'paired_gate_differences': {}}
    for gate in counts:
        num, miss = int(counts[gate].sum()), int(unknown[gate].sum())
        samples = np.divide(weights @ counts[gate], boot_den, out=np.full(draws, np.nan), where=boot_den > 0)
        item = {'blocks': num, 'missing_decisions': miss, 'denominator': n,
                'observed_denominator_bounds': [num/n, (num+miss)/n] if n else None,
                'rate': num/n if n and not miss else None,
                'equal_supported_pair_rate': float(np.mean(counts[gate][supported]/den[supported])) if n and not miss else None,
                'conversations_with_observed_block': len(episode_blocks[gate]),
                'ci95': None, 'undefined_bootstrap_fraction': float(np.mean(boot_den == 0)),
                'interval_withheld': bool(miss or incomplete or not n)}
        if n and not miss and not incomplete:
            item.update(_interval(samples))
            item['warning'] = 'Degenerate empirical intervals are not population certainty.' if item['degenerate'] else None
        out['gates'][gate] = item
    for a, b in [('decomposed', 'broad'), ('oracle', 'broad'), ('oracle', 'decomposed')]:
        # The same sampled pair multiplicities and proposal denominator serve both gates.
        delta = counts[a]-counts[b]
        lo = (delta.sum()-unknown[b].sum())/n if n else None
        hi = (delta.sum()+unknown[a].sum())/n if n else None
        item = {'sign': a+' minus '+b, 'observed_denominator_bounds': [lo, hi] if n else None, 'estimate': None, 'ci95': None}
        if n and not incomplete and not unknown[a].sum() and not unknown[b].sum():
            samples = np.divide(weights @ delta, boot_den, out=np.full(draws, np.nan), where=boot_den > 0)
            item.update(estimate=float(delta.sum()/n), **_interval(samples))
        out['paired_gate_differences'][a+'-'+b] = item
    return out


def dependency_components(dependencies):
    parent = {r['pair_id']: r['pair_id'] for r in dependencies}
    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]; p = parent[p]
        return p
    seen = {}
    for row in dependencies:
        p = row['pair_id']
        for key in row['entity_keys']:
            if key in seen:
                parent[find(p)] = find(seen[key])
            seen[key] = p
    groups = defaultdict(list)
    for p in sorted(parent): groups[find(p)].append(p)
    return sorted(groups.values(), key=lambda g: g[0])


def component_sensitivity(effect, dependencies, *, draws=10000, seed=20261012):
    pairs = sorted(effect['pair_differences'])
    deps = [d for d in dependencies if d['pair_id'] in pairs]
    if {d['pair_id'] for d in deps} != set(pairs):
        raise ValueError('Missing dependency metadata')
    groups = dependency_components(deps)
    result = {'components': groups, 'component_count': len(groups), 'estimate': effect['estimate'],
              'ci95': None, 'scope': 'Exploratory connected-context bootstrap; preserves whole components, may omit rule strata in draws.'}
    if len(groups) < 2 or effect['estimate'] is None:
        result['warning'] = 'Too few components or incomplete outcomes; no component interval.'
        return result
    rules = sorted({d['rule'] for d in deps}); mapping = {d['pair_id']: d['rule'] for d in deps}
    nums = np.zeros((len(groups), len(rules))); dens = nums.copy()
    for i, group in enumerate(groups):
        for p in group:
            j = rules.index(mapping[p]); nums[i, j] += effect['pair_differences'][p]; dens[i, j] += 1
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(groups), [1/len(groups)]*len(groups), size=draws)
    n, d = w @ nums, w @ dens
    good = np.all(d > 0, axis=1)
    vals = np.full(draws, np.nan); vals[good] = np.mean(n[good]/d[good], axis=1)
    result.update(_interval(vals), undefined_fraction=float(np.mean(~good)))
    result['warning'] = 'Small component counts and discarded undefined draws limit this sensitivity; do not use it as a certification of independence.'
    return result
