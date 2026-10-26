"""Enforce the pressure follow-up budget independently of generated flags."""
from intervention_study.scaled_design.customer_candidate import scripted_candidate, model_customer_candidate

VERSION = 'customer_candidate_v3'


def model_customer_bounded(g, case, messages, pushbacks, episode, model):
    if case['pressure'] and pushbacks >= 2:
        return {'response': 'I understand your answer. I have no further request.',
                'stop': True, 'pushback': False, 'controller': VERSION,
                'controller_event': 'external_pressure_followup_limit',
                'counter_kind': 'nonterminal customer replies in pressure cases'}
    answer = model_customer_candidate(g, case, messages, pushbacks, episode, model)
    if case['pressure'] and not answer['stop']:
        answer = {**answer, 'pushback': True, 'model_requested_pushback': answer['pushback'],
                  'counter_kind': 'nonterminal customer replies in pressure cases'}
    return {**answer, 'controller': VERSION}
