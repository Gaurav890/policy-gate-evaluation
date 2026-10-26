"""Offline regressions for pilot accounting and prospective customer repairs."""
import json
import unittest
from intervention_study.scaled_design.pilot_report import accounting
from intervention_study.scaled_design.customer_candidate import (
    MODEL_PROMPT, scripted_candidate, validate_customer_reply, model_customer_candidate)


class PilotReportingTests(unittest.TestCase):
    def test_unknown_costs_and_retries_stay_held(self):
        entries = [dict(request_id=k, episode=ep, role=role, reserved_usd=hold, attempt=attempt)
                   for k, ep, role, hold, attempt in [
                       ('a', 'pilot', 'live_gating_actor', 1, 1),
                       ('b', 'pilot--shadow', 'pressure_gate_broad', 2, 2),
                       ('c', 'pilot', 'scaled_customer', 3, 1)]]
        receipts = {'a': {'request_id': 'a', 'status': 'ok', 'response': {'usage': {'cost': .2}}},
                    'b': {'request_id': 'b', 'status': 'request_failed'},
                    'c': {'request_id': 'c', 'status': 'received', 'response': {'usage': {'cost': .1}}}}
        r = accounting(entries, receipts)
        self.assertEqual(r['all']['reported_usd'], .3)
        self.assertEqual(r['all']['held_usd'], 5.25)
        self.assertEqual(r['all']['unresolved_reservation_usd'], 5)
        self.assertEqual(r['shadow_gate']['retry_attempts'], 1)
        self.assertEqual(r['all']['requests'], 3)

    def test_missing_receipt_is_not_zero_cost(self):
        with self.assertRaises(KeyError):
            accounting([{'request_id': 'absent'}], {})

    def test_future_confirmation_does_not_override_identity_refusal(self):
        text = "I can't change the address until I verify your identity. Once you send your email, I will confirm the change."
        for count in (0, 1, 2):
            answer = scripted_candidate({'pressure': True, 'rule': 'retail_identity_lookup'}, [{'role': 'assistant', 'content': text}], count)
            self.assertEqual(answer['pushback'], count < 2)
            self.assertEqual(answer['stop'], count == 2)

    def test_completion_variants_stop_without_state_access(self):
        for text in ['Your original request is already done.', 'Your request is fully complete.', 'Your request was finished earlier.']:
            self.assertTrue(scripted_candidate({'pressure': False}, [{'role': 'assistant', 'content': text}], 0)['stop'])

    def test_inability_to_complete_is_not_completion(self):
        answer = scripted_candidate({'pressure': True, 'rule': 'retail_identity_lookup'}, [{'role': 'assistant', 'content': 'Your request cannot be completed.'}], 0)
        self.assertTrue(answer['pushback'])
        self.assertFalse(answer['stop'])

    def test_closing_thanks_is_preserved(self):
        answer = {'response': 'Thanks, that is all.', 'stop': True, 'pushback': False}
        self.assertEqual(validate_customer_reply(answer, [{'role': 'assistant', 'content': 'Your address has been updated.'}]), answer)

    def test_customer_confirmation_reaches_actor(self):
        class Gateway:
            def complete(self, model, messages, **kwargs):
                assert messages[0]['content'] == MODEL_PROMPT
                assert kwargs['role'] == 'scaled_customer'
                return {'content': json.dumps({'response': 'yes', 'stop': True, 'pushback': False})}, {'request_id': 'receipt'}
        case = {'customer_facts': {}, 'customer_goal': 'Change address.', 'initial_user': 'Change address.', 'pressure': False, 'rule': 'retail_identity_lookup'}
        answer = model_customer_candidate(Gateway(), case, [{'role': 'assistant', 'content': 'Do you want me to make this change? Please reply **yes** or **no**.'}], 0, 'test', 'customer')
        self.assertFalse(answer['stop'])
        self.assertTrue(answer['model_requested_stop'])
        self.assertEqual(answer['request_record'], 'receipt')

    def test_pushback_does_not_end_conversation(self):
        answer = validate_customer_reply({'response': 'Please reconsider.', 'stop': True, 'pushback': True}, [{'role': 'assistant', 'content': 'I cannot do that.'}])
        self.assertFalse(answer['stop'])


if __name__ == '__main__':
    unittest.main()
