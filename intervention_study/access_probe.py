"""Small recorded model/tool/schema access checks, excluded from study outcomes."""
import argparse
import json
from intervention_study.common import BASE, save, verify_freeze
from intervention_study.runtime import gateway
from gateway_budget import BudgetExceeded

def main():
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--actor',required=True);a=p.parse_args();assert a.live
    cfg=verify_freeze();g=gateway(cfg['pilot_cumulative_ceiling_usd']);path=BASE/'access_probes'/(a.actor+'.json')
    assert not path.exists(),'Probe already recorded; inspect it instead of silently repeating.'
    record={'model':a.actor,'status':'started','request_records':[]};save(path,record)
    messages=[{'role':'user','content':'Call echo with value "ping". After its result, reply only with JSON {"ok":true}.'}]
    tool={'type':'function','function':{'name':'echo','description':'Return the input text.','parameters':{'type':'object','properties':{'value':{'type':'string'}},'required':['value'],'additionalProperties':False}}}
    try:
        message,r=g.complete(a.actor,messages,tools=[tool],max_tokens=4096,role='pressure_probe',episode='intervention-probe-'+a.actor);record['request_records'].append(r['request_id'])
        calls=message.get('tool_calls') or [];assert len(calls)==1 and calls[0]['function']['name']=='echo'
        assert json.loads(calls[0]['function']['arguments'])=={'value':'ping'}
        messages.append({k:v for k,v in message.items() if k in ['role','content','tool_calls','reasoning','reasoning_details'] and v is not None})
        messages.append({'role':'tool','tool_call_id':calls[0]['id'],'content':'"ping"'})
        fmt={'type':'json_schema','json_schema':{'name':'probe','strict':True,'schema':{'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok'],'additionalProperties':False}}}
        message,r=g.complete(a.actor,messages,max_tokens=4096,role='pressure_probe',episode='intervention-probe-'+a.actor,response_format=fmt);record['request_records'].append(r['request_id'])
        assert json.loads(message['content'])=={'ok':True};record['status']='completed';record['last_usage']=r['response'].get('usage',{})
    except Exception as exc:
        record.update(status='incomplete',error=type(exc).__name__)
        if isinstance(exc,BudgetExceeded):raise
    finally:save(path,record)
    print(json.dumps(record),flush=True)

if __name__=='__main__':main()
