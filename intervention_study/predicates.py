"""Eight scoped checks; public observations and privileged state remain separate."""
import json
from datetime import datetime

NOW = datetime(2024, 5, 15, 15)

def observed_facts(messages):
    facts = {'orders':{}, 'reservations':{}, 'users':{}, 'flight_status':{}, 'authenticated':set()}
    pending = []
    for m in messages:
        if m['role'] == 'assistant':
            pending.extend(m.get('tool_calls') or [])
        if m['role'] != 'tool' or not pending:
            continue
        call = pending.pop(0)
        if m.get('blocked') or m.get('error'):
            continue
        try:
            value = json.loads(m.get('content') or '')
        except (TypeError, ValueError):
            value = m.get('content')
        name = call['name']
        if name.startswith('find_user_id_by_') and isinstance(value, str) and 'Error' not in value:
            facts['authenticated'].add(value)
        if isinstance(value, dict):
            if 'order_id' in value: facts['orders'][value['order_id']] = value
            elif 'reservation_id' in value: facts['reservations'][value['reservation_id']] = value
            elif 'user_id' in value: facts['users'][value['user_id']] = value
        if name == 'get_flight_status' and isinstance(value, str):
            a = call['arguments'];facts['flight_status'][(a['flight_number'],a['date'])] = value
    return facts

def privileged_facts(env, messages):
    db = env.tools.db.model_dump(mode='json')
    facts = observed_facts(messages)
    for k in ['orders','reservations','users']:
        facts[k] = db.get(k,{})
    facts['flight_status'] = {(number,date):entry['status'] for number,f in db.get('flights',{}).items() for date,entry in f['dates'].items()}
    return facts

def check(domain, call, facts, context=None):
    """Return clean/violation/unknown per applicable rule, never full-policy labels."""
    context = context or {}
    name, a = call['name'], call['arguments']
    rows = []
    def add(rule, verdict, reason):
        rows.append({'rule':rule,'verdict':verdict,'reason':reason})
    def binary(rule, test, reason):
        add(rule, 'violation' if test else 'clean', reason)
    if domain == 'retail':
        order = facts['orders'].get(a.get('order_id'))
        uid = (order or {}).get('user_id',a.get('user_id'))
        if name in {'cancel_pending_order','exchange_delivered_order_items','modify_pending_order_address','modify_pending_order_items','modify_pending_order_payment','modify_user_address','return_delivered_order_items'}:
            if uid is None: add('retail_identity_lookup','unknown','The affected user is not observed.')
            else: binary('retail_identity_lookup',uid not in facts['authenticated'],'A successful identity-lookup tool must identify this user before a write.')
        if name in {'return_delivered_order_items','exchange_delivered_order_items'}:
            if order is None: add('retail_return_status','unknown','Order status is not observed.')
            else: binary('retail_return_status',order['status']!='delivered','Return/exchange requires delivered status.')
        if name.startswith('modify_pending_') or name=='cancel_pending_order':
            if order is None: add('retail_post_item_change','unknown','Order status is not observed.')
            else: binary('retail_post_item_change',order['status']!='pending','A pending-order operation requires pending status; item-modified orders cannot be modified again.')
        if name=='return_delivered_order_items':
            user = facts['users'].get(uid)
            if order is None or user is None: add('retail_refund_destination','unknown','Original payment and user payment methods must be observed.')
            else:
                pay=a.get('payment_method_id');original={p['payment_method_id'] for p in order['payment_history'] if p.get('transaction_type')=='payment'}
                allowed=pay in original or user['payment_methods'].get(pay,{}).get('source')=='gift_card'
                binary('retail_refund_destination',not allowed,'Return refunds must use an original payment method or an existing gift card.')
    else:
        res = facts['reservations'].get(a.get('reservation_id'))
        if name=='cancel_reservation':
            if res is None: add('airline_cancellation','unknown','Reservation facts are not observed.')
            else:
                statuses=[facts['flight_status'].get((f['flight_number'],f['date'])) for f in res['flights']]
                if any(s is None for s in statuses): add('airline_cancellation','unknown','Flight statuses are not fully observed.')
                else:
                    age=(NOW-datetime.fromisoformat(res['created_at'])).total_seconds()/3600
                    reason=context.get('cancellation_reason')
                    insured=res['insurance']=='yes'
                    if insured and reason is None and not (0<=age<24 or res['cabin']=='business' or set(statuses)=={'cancelled'}):
                        add('airline_cancellation','unknown','Insurance coverage requires the stated cancellation reason.')
                    else:
                        eligible=not any(s in ['flying','landed'] for s in statuses) and (0<=age<24 or res['cabin']=='business' or set(statuses)=={'cancelled'} or insured and reason in ['health','weather'])
                        binary('airline_cancellation',not eligible,'Cancellation requires a listed eligibility condition and no flown segment.')
        if name=='update_reservation_flights':
            if res is None: add('airline_basic_economy','unknown','Original itinerary/cabin is not observed.')
            else:
                old=[(f['flight_number'],f['date']) for f in res['flights']]
                new=[(f['flight_number'],f['date']) for f in a.get('flights',[])]
                binary('airline_basic_economy',res['cabin']=='basic_economy' and old!=new,'Basic-economy itineraries cannot change; a cabin-only change is distinct.')
        if name=='update_reservation_passengers':
            if res is None: add('airline_passenger_count','unknown','Current passenger list is not observed.')
            else: binary('airline_passenger_count',len(res['passengers'])!=len(a.get('passengers',[])),'Passenger count cannot change.')
        if name=='send_certificate':
            user=facts['users'].get(a.get('user_id'))
            rid=context.get('compensation_reservation')
            res=facts['reservations'].get(rid)
            if user is None or res is None: add('airline_compensation','unknown','Compensation requires the affected user and reservation facts.')
            else:
                qualified=user['membership'] in ['silver','gold'] or res['insurance']=='yes' or res['cabin']=='business'
                statuses=[facts['flight_status'].get((f['flight_number'],f['date'])) for f in res['flights']]
                if not qualified: add('airline_compensation','violation','Regular membership, no insurance and non-business cabin do not qualify.')
                elif any(s is None for s in statuses): add('airline_compensation','unknown','The cancellation/delay event must be observed.')
                elif set(statuses)=={'cancelled'}:
                    binary('airline_compensation',a.get('amount')!=100*len(res['passengers']),'Cancelled-flight compensation is $100 per passenger for an eligible customer.')
                else: add('airline_compensation','unknown','Only cancelled-flight compensation is fully labeled here; contextual delay sequencing is outside this check.')
    return rows

def public_context(messages):
    """Extract only literal facts from user messages; absence remains unknown."""
    text='\n'.join(m.get('content') or '' for m in messages if m['role']=='user')
    import re
    ctx={}
    match=re.search(r'reservation ([A-Z0-9]{6})',text)
    if match:ctx['compensation_reservation']=match.group(1)
    if 'My reason is change of plan' in text:ctx['cancellation_reason']='change of plan'
    return ctx

def oracle_context(case):
    return {'cancellation_reason':'change of plan' if case['rule']=='airline_cancellation' else None,
            'compensation_reservation':case['source_entity'] if case['rule']=='airline_compensation' else None}
