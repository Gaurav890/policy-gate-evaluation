"""Prepare the primary configuration without authorizing collection."""
from pathlib import Path
from intervention_study.common import ROOT, read, save, digest
from intervention_study.primary_study.statistics import dependency_components

BASE = Path(__file__).resolve().parent
PILOT = ROOT/'intervention_study/scaled_design'


def main():
    if (BASE/'freeze.json').exists():
        raise RuntimeError('Primary configuration is frozen; amendments need separate retained versions')
    if list((BASE/'episodes').glob('*.json')) or list((BASE/'shadow').glob('*.json')):
        raise RuntimeError('Cannot regenerate a configuration after collection begins')
    allocation = read(PILOT/'allocation.json')
    for c in allocation:
        c['episode'] = c['episode'].replace('scaled-evaluation--', 'primary-evaluation-20261012--')
    assert len(allocation)==4608 and len({c['episode'] for c in allocation})==4608
    save(BASE/'allocation.json', allocation)
    deps = read(PILOT/'dependencies.json'); save(BASE/'dependencies.json', deps)
    old = read(PILOT/'protocol.json')
    cfg = {k: old[k] for k in ['models','actors','gate_model','customer_model','conditions','max_actor_turns','max_customer_turns','output_cap','threshold','primary_conversations','customer_extension_conversations','total_conversations','shadow_source_conversations','source_pairs','customer_extension_pairs','repeats','schedule_seed','case_manifest_sha256','model_catalog_sha256']}
    cfg.update(version=1, status='Prepared primary study; funding and collection locked',
        customer_version='customer_candidate_v3', bootstrap_draws=10000, primary_contrast_count=6,
        descriptive_expanded_quantile_level=1-.05/6,
        formal_inference='Six two-sided source-pair label-swap randomization tests, Holm-adjusted at 0.05; exact sharp-null interpretation requires assignment exchangeability, stable potential outcomes and no inter-run interference. Missing contrasts keep their family slot and receive no p value.',
        bootstrap_interpretation='Descriptive only. The preserved prospective calibration found anti-conservative percentile intervals; neither the nominal 95% nor nominal multiplicity-expanded intervals establish their advertised coverage.',
        controller_specification={'scripted':'Tested scripted_candidate: refusal precedence and completion variants; at most two flagged pushbacks.',
          'model_customer':'Tested model_customer_bounded: every nonterminal reply on a pressure task consumes one of two follow-ups, then the controller closes without another model call.',
          'comparison':'A controller-package robustness comparison; generation and pressure-count semantics differ. Not a pure test of natural-language variation.'},
        primary_estimand='Equal rule and source-pair weighted gate-minus-no-gate differences for pressure executed violations and permitted completed service, scripted customer.',
        source_bootstrap='10000 resamples of source pairs within fixed rule strata; preserve all actor/repeat/condition observations.',
        shadow_estimand='Pooled-proposal block rate by mechanical class and paired gate differences; supported-pair mean as sensitivity.',
        missingness='Unstarted/infrastructure-interrupted outcomes unresolved; observed positives retained; administrative turn limits are fixed-horizon outcomes. Shadow missing decisions never equal allows.',
        exception_policy='Stop on inference/schema failures; retain all original attempts and checkpointed partial scores. No silent retries or replacement episodes.',
        customer_flags='Literal/structural checks; no automatic correction or primary exclusion. Pair-level exclusions exploratory only.',
        scope='Eight fixed rules, two benchmark domains, 48 designed source pairs and three configured actors. No full-policy or deployment safety claim.',
        allocation_sha256=digest(BASE/'allocation.json'), dependencies_sha256=digest(BASE/'dependencies.json'),
        proposed_cumulative_ceiling_usd=1250, funding_approval_record='authorization.json',
        sequential_policy='Fixed allocation. No stopping, dropping tasks or selecting models based on outcomes or significance.',
        schedule_scope='Condition/request order randomized within source-pair/actor/repeat/customer blocks; actors unseeded, customer and actor blocks not randomly reordered.',
        paper_strategy='One combined paper; not submitted.')
    save(BASE/'protocol.json', cfg)
    if not (BASE/'authorization.json').exists() or read(BASE/'authorization.json').get('approved') is False:
        save(BASE/'authorization.json', {'approved':False,'scope':'primary_live_and_shadow','protocol_sha256':digest(BASE/'protocol.json'),
            'cumulative_ceiling_usd':None,'reason':'The $125 pilot approval does not authorize the full primary study.'})
    save(BASE/'dependency_summary.json', {'source_pairs':48,'components':dependency_components(deps),
        'warning':'Recorded shared entities are a sensitivity grouping, not proof of independence; all tasks share rule templates and domains.'})
    print('Prepared 4608 cells and the primary protocol. Collection remains unapproved.')


if __name__=='__main__':main()
