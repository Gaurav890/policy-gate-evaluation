"""Assumption-based Monte Carlo sensitivity; no model calls or fitted pilot effects."""
from pathlib import Path
import numpy as np
from intervention_study.common import save
from intervention_study.primary_study.statistics import bootstrap_weights, holm_adjust

BASE = Path(__file__).resolve().parent


def simulate(base_risk, rho, reduction, simulations=600, draws=2000, seed=20261012):
    rng = np.random.default_rng(seed)
    rules = [str(r) for r in range(8) for _ in range(6)]
    weights = bootstrap_weights(rules, draws, seed+1).astype(float)/48
    signs = (2*np.random.default_rng(seed+2).integers(0,2,size=(draws,48))-1)/48
    effects = np.zeros((simulations, 6, 48))
    for metric, mean_risk in enumerate([base_risk, .9]):
        if rho:
            strength = 1/rho-1
            latent = rng.beta(mean_risk*strength, (1-mean_risk)*strength, size=(simulations,48))
        else:
            latent = np.full((simulations,48),mean_risk)
        baseline = rng.binomial(9, latent)/9
        for gate in range(3):
            rate = latent*(1-reduction/base_risk) if metric==0 else latent
            treated = rng.binomial(9, rate)/9
            effects[:, gate*2+metric, :] = treated-baseline
    lo = np.zeros((simulations,6)); hi = lo.copy(); width = lo.copy()
    adjusted = lo.copy()
    for i in range(simulations):
        values = weights @ effects[i].T
        q = np.quantile(values, [.025/6, 1-.025/6], axis=0)
        lo[i], hi[i] = q
        width[i] = q[1]-q[0]
        observed = effects[i].mean(axis=1)
        permuted = signs @ effects[i].T
        p_values = (1+np.sum(np.abs(permuted) >= np.abs(observed)[None,:]-1e-12,axis=0))/(draws+1)
        adjusted[i] = holm_adjust(p_values.tolist())
    truth = np.tile([-reduction, 0.0], 3)
    misses = (lo>truth)|(hi<truth)
    rejects_zero = (lo>0)|(hi<0)
    family_noncoverage = float(np.mean(np.any(misses, axis=1)))
    power = float(np.mean(hi[:,0]<0))
    randomization_detection = float(np.mean((adjusted[:,0]<.05)&(effects[:,0,:].mean(axis=1)<0)))
    true_nulls = np.isclose(truth,0)
    randomization_false_positive = float(np.mean(np.any(adjusted[:,true_nulls]<.05,axis=1)))
    return {'baseline_violation_risk_assumed':base_risk,'within_pair_latent_correlation_assumed':rho,
            'absolute_risk_reduction_assumed':reduction,'simulated_datasets':simulations,'bootstrap_draws_per_dataset':draws,
            'family_noncoverage_fraction':family_noncoverage,
            'family_noncoverage_monte_carlo_se':float(np.sqrt(family_noncoverage*(1-family_noncoverage)/simulations)),
            'first_gate_detection_fraction':power,'detection_monte_carlo_se':float(np.sqrt(power*(1-power)/simulations)),
            'holm_randomization_first_gate_detection_fraction':randomization_detection,
            'holm_randomization_detection_monte_carlo_se':float(np.sqrt(randomization_detection*(1-randomization_detection)/simulations)),
            'holm_randomization_any_true_null_false_positive_fraction':randomization_false_positive,
            'holm_randomization_false_positive_monte_carlo_se':float(np.sqrt(randomization_false_positive*(1-randomization_false_positive)/simulations)),
            'median_adjusted_interval_width_violation':float(np.median(width[:,0])),
            'family_false_positive_fraction_under_global_null':float(np.mean(np.any(rejects_zero,axis=1))) if reduction==0 else None}


def main():
    scenarios = [simulate(p,rho,reduction,seed=20261012+i)
                 for i,(p,rho,reduction) in enumerate((p,rho,d) for p in [.02,.1,.3] for rho in [0,.2,.5] for d in [0,p/2])]
    save(BASE/'precision_scenarios.json', {'scope':'Prospective sensitivity calculations, not empirical results or guaranteed power.',
        'design':{'pairs':48,'rule_strata':8,'pairs_per_rule':6,'rollouts_per_pair_arm':9,'primary_contrasts':6},
        'amendment':'Before any primary collection, formal comparisons changed to sharp-null paired randomization tests with Holm adjustment. Bootstrap coverage diagnostics are preserved, and bootstrap intervals remain descriptive.',
        'assumptions':['Independent source pairs conditional on fixed strata.',
            'Exchangeable actor/repeat observations conditional on beta-distributed pair difficulty; no fitted actor-family effects.',
            'Independent treatment rollouts conditional on the shared pair difficulty.',
            'Permitted-service risk is 0.9 with no treatment effect; all three gates share the same assumed violation reduction.',
            'Complete collection, stable model behavior, correct covered labels and no simulator errors.',
            '2000 bootstrap draws used for resource-bounded design calibration; production summaries use 10000.',
            '2000 sign-flip draws with a plus-one correction per test; production uses 10000. Holm adjusts the six prespecified tests.',
            'Null simulated arm counts are exchangeable conditional on the shared difficulty. This checks that model, not every weak mean-null or deployment distribution.',
            'Nominal percentile intervals can miss their advertised coverage, especially with rare outcomes. Small clusters and dependencies remain material.'],
        'scenarios':scenarios})
    for s in scenarios:
        print(s['baseline_violation_risk_assumed'],s['within_pair_latent_correlation_assumed'],s['absolute_risk_reduction_assumed'],
              'randomization_detection',round(s['holm_randomization_first_gate_detection_fraction'],3),
              'randomization_false_positive',round(s['holm_randomization_any_true_null_false_positive_fraction'],3),
              'bootstrap_noncoverage',round(s['family_noncoverage_fraction'],3),flush=True)


if __name__=='__main__':main()
