"""Synthetic precision scenarios for the amended design, without model requests."""
import numpy as np
from pathlib import Path
from intervention_study.common import save


def scenario(risk, rho, relative_reduction, seed, simulations=600, draws=2000):
    rng=np.random.default_rng(seed)
    effects=np.zeros((simulations,4,32))
    for metric,mean in enumerate([risk,.9]):
        if rho:
            strength=1/rho-1
            latent=rng.beta(mean*strength,(1-mean)*strength,size=(simulations,32))
        else:
            latent=np.full((simulations,32),mean)
        baseline=rng.binomial(6,latent)/6
        for gate in range(2):
            probability=latent*(1-relative_reduction) if metric==0 else latent
            effects[:,gate*2+metric,:]=rng.binomial(6,probability)/6-baseline
    observed=effects.mean(axis=2)
    signs=2*rng.integers(0,2,size=(draws,32))-1
    raw=[]
    for contrast in range(4):
        permuted=signs @ effects[:,contrast,:].T /32
        raw.append((1+np.sum(np.abs(permuted)>=np.abs(observed[:,contrast])[None,:]-1e-12,axis=0))/(draws+1))
    raw=np.array(raw).T
    order=np.argsort(raw,axis=1,kind='stable')
    ordered=np.take_along_axis(raw,order,axis=1)
    adjusted=np.minimum(1,np.maximum.accumulate(ordered*np.arange(4,0,-1),axis=1))
    adjusted=np.take_along_axis(adjusted,np.argsort(order,axis=1),axis=1)
    true_null=[0,1,2,3] if relative_reduction==0 else [1,3]
    fp=float(np.mean(np.any(adjusted[:,true_null]<.05,axis=1)))
    detection=float(np.mean((adjusted[:,0]<.05)&(observed[:,0]<0)))
    return {'baseline_violation_risk_assumed':risk,'within_pair_correlation_assumed':rho,
        'relative_violation_reduction_assumed':relative_reduction,'simulated_datasets':simulations,
        'randomization_draws_per_dataset':draws,'first_gate_detection_fraction':detection,
        'detection_monte_carlo_se':float(np.sqrt(detection*(1-detection)/simulations)),
        'any_true_null_rejection_fraction':fp,'false_positive_monte_carlo_se':float(np.sqrt(fp*(1-fp)/simulations))}


if __name__=='__main__':
    combinations=[(p,rho,d) for p in [.02,.1,.3] for rho in [0,.2,.5] for d in [0,.5]]
    rows=[scenario(*args,seed=20261013+i) for i,args in enumerate(combinations)]
    save(Path(__file__).resolve().parent/'precision_scenarios.json',{
        'design':{'source_pairs':32,'pairs_per_rule':4,'observations_per_pair_arm':6,'comparisons':4},
        'scope':'Unfitted synthetic assumptions, not empirical findings or a validated statistical minimum. Tests remain exploratory after a post-start amendment.',
        'assumptions':['Independent pairs with shared beta-distributed difficulty within pairs.',
            'Exchangeable actor/repeat observations; actor-family heterogeneity not modeled.',
            'Independent condition rollouts conditional on pair difficulty; fixed rules weighted equally.',
            'Permitted service probability 0.9 and no treatment effect; common violation reduction for both gates.',
            'Complete outcomes, correct selected labels and no infrastructure failures. Actual inherited interruption violates complete-data assumption.',
            'Synthetic 2000-draw tests; actual descriptive sensitivity uses 10000 draws. Shared-context dependence and hosted-model drift are not represented.'],
        'scenarios':rows})
    print('Saved 18 synthetic scenarios, 10800 datasets; no API calls.')
