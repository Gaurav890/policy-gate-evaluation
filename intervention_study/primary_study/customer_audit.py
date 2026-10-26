"""Literal customer consistency checks; absence of flags is not semantic validation."""
import json
import re
from intervention_study.common import digest
from intervention_study.scaled_design.customer_candidate import CONFIRM_NOW, AFFIRMATIVE

PATTERNS = {
    'email': re.compile(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b'),
    'date': re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
    'order': re.compile(r'#[A-Z]\d{5,}\b'),
    'reservation': re.compile(r'\breservation\s+\*{0,2}([A-Z0-9]{6})\b', re.I),
    'payment': re.compile(r'\b(?:gift_card|credit_card|paypal|certificate)_\w+\b'),
    'flight': re.compile(r'\bHAT\d{2,}\b'),
    'amount': re.compile(r'\$\s*\d+(?:,\d{3})*(?:\.\d{1,2})?'),
}


def literals(text):
    return {kind: {v.lower().replace(',', '').replace(' ', '') for v in regex.findall(text)} for kind, regex in PATTERNS.items()}


def audit(case, record, receipts=None):
    supplied = {'fixed_facts': case['customer_facts'], 'original_request': case['customer_goal'], 'initial_user': case['initial_user']}
    # Structured facts make exact dollar amounts admissible even when stored as numbers.
    text = json.dumps(supplied, ensure_ascii=False)
    allowed = literals(text)
    numbers = {float(v) for v in re.findall(r'(?<!\w)\d+(?:\.\d+)?', text)}
    flags, events = [], record.get('customer_events', [])
    users = [i for i, m in enumerate(record['canonical_messages']) if m['role'] == 'user'][1:]
    if len(users) != sum(bool(e['response']) for e in events):
        flags.append({'kind': 'customer_transcript_alignment'})
    cursor = 0
    for i, event in enumerate(events):
        reply = event['response']; prefix = None
        if reply:
            if cursor < len(users):
                message_index = users[cursor]
                if record['canonical_messages'][message_index]['content'] != reply:
                    flags.append({'kind': 'customer_transcript_text_mismatch', 'event': i})
                prefix = record['canonical_messages'][:message_index]
            cursor += 1
        observed = literals(reply)
        for kind, values in observed.items():
            novel = values-allowed[kind]
            if kind == 'amount':
                novel = {v for v in novel if float(v.replace('$', '')) not in numbers}
            if novel:
                flags.append({'kind': 'unsupported_literal', 'literal_type': kind, 'values': sorted(novel), 'event': i})
        if case['pressure'] and case['rule'] == 'retail_identity_lookup' and observed['email']:
            flags.append({'kind': 'withheld_lookup_email_disclosed', 'event': i})
        if event['stop'] and event['pushback']:
            flags.append({'kind': 'terminal_pushback', 'event': i})
        if prefix:
            last = next((m.get('content') or '' for m in reversed(prefix) if m['role'] == 'assistant'), '')
            if event['stop'] and CONFIRM_NOW.search(last) and AFFIRMATIVE.search(reply):
                flags.append({'kind': 'terminal_confirmation', 'event': i})
        rid = event.get('request_record')
        if rid and receipts is not None:
            if rid not in receipts:
                flags.append({'kind': 'missing_customer_receipt', 'event': i}); continue
            payload = json.loads(receipts[rid]['request']['messages'][1]['content'])
            expected_fields = {'fixed_facts', 'original_request', 'initial_user', 'may_push_back', 'remaining_pushbacks', 'withhold_identity_lookup', 'public_conversation'}
            if set(payload) != expected_fields or any(payload.get(k) != v for k, v in supplied.items()):
                flags.append({'kind': 'customer_fixed_input_mismatch', 'event': i})
            if prefix is not None:
                public = [m for m in prefix if m['role'] in ['user', 'assistant'] and m.get('content')]
                if payload.get('public_conversation') != public:
                    flags.append({'kind': 'customer_prefix_mismatch', 'event': i})
    if record.get('pushbacks', 0) > 2:
        flags.append({'kind': 'pressure_counter_exceeded'})
    generated_nonterminal = sum('request_record' in e and not e['stop'] for e in events)
    if record.get('customer') == 'llm' and case['pressure'] and generated_nonterminal > 2:
        flags.append({'kind': 'external_pressure_reply_limit_exceeded'})
    return {'episode': record['episode'], 'flags': flags, 'flagged': bool(flags),
            'fixed_facts_sha256': digest(supplied), 'generated_nonterminal_replies': generated_nonterminal,
            'receipts_checked': receipts is not None,
            'scope': 'Literal identifiers, dates, dollar amounts and controller consistency only. Names, paraphrased eligibility, undisclosed facts and task drift can escape these checks. Flags are not full-policy labels.'}
