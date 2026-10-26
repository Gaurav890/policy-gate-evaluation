"""Small empirical capability check, not a guarantee for all requests."""
from gateway_budget import ROOT, Budget, write_json
from gateway_v2 import Gateway
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');a=p.parse_args()
    if not a.live:raise SystemExit('--live required')
    target=ROOT/'groundwork/serial_probe_v002.json'
    if target.exists():raise SystemExit('Probe already recorded')
    tools=[{'type':'function','function':{'name':'get_weather','description':'Look up city weather','parameters':{'type':'object','properties':{'city':{'type':'string'}},'required':['city'],'additionalProperties':False}}}]
    g=Gateway(Budget(ceiling=22),serial_tools=True)
    results=[]
    for city in ['Boston and Seattle','Paris and Rome']:
        m,r=g.complete('deepseek',[{'role':'user','content':f'Use the weather tool to retrieve weather for {city}. Call the tool for both cities now.'}],tools=tools,max_tokens=512,role='access_probe',episode='serial-probe-v002')
        count=len(m.get('tool_calls') or [])
        results.append({'request_id':r['request_id'],'tool_call_count':count,'accepted_single_call':count==1})
    write_json(target,{'results':results,'all_passed':all(x['accepted_single_call'] for x in results),
        'limitation':'Empirical response check only; serial setting not listed in catalog. Runtime guard stops before execution if a provider emits multiple calls.'})
    print(results)
