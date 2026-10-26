"""Preserve failed first-pilot evidence and freeze a smaller engineering recovery pilot."""
from intervention_study.common import BASE, ROOT, read, save, digest, verify_freeze

def main():
    verify_freeze();assert not (BASE/'freeze_v2.json').exists()
    cfg=read(BASE/'protocol.json')
    cfg.update(version=2,status='Engineering recovery pilot; evaluation remains locked',
      amendment={'reason':'119 request failures (116 connection errors, 3 timeouts) plus premature customer stop at confirmation. First-pilot records remain immutable and are not effectiveness evidence.',
                 'changes':['Free connection preflight before every inference reservation','Shared stop after first transport/unusable-output failure','Explicit customer stop instructions and a recorded override for leading confirmation replies','32 fixed recovery conversations spanning two rule pairs and every original actor/gate pilot stratum; no outcome-based pair selection','All other task facts, actor/monitor prompts and native tools unchanged'],
                 'limitations':'Two-rule recovery pilot cannot estimate eight-rule population effects. No inference about strong reasoning merely from a requested effort setting. Unresolved first-pilot reservations remain held.'})
    cfg['recovery_rules']=['airline_cancellation','retail_post_item_change']
    cells=[{**c,'episode':c['episode'].replace('intervention-','intervention-v2-',1)} for c in read(BASE/'pilot_allocation.json') if c['rule'] in cfg['recovery_rules']]
    # Round-robin fixed actor/condition groups so interruption does not leave all expensive configurations until last.
    groups={}
    for cell in cells:groups.setdefault((cell['actor'],cell['condition']),[]).append(cell)
    for group in groups.values():group.sort(key=lambda c:digest(c['episode']))
    cells=[group[i] for i in range(4) for key,group in sorted(groups.items())];assert len(cells)==32
    save(BASE/'protocol_v2.json',cfg);save(BASE/'pilot_allocation_v2.json',cells)
    files=[BASE/n for n in ['runtime_guarded.py','runner_v2.py','verify_v2.py','prepare_v2.py','protocol_v2.json','pilot_allocation_v2.json']]
    save(BASE/'freeze_v2.json',{'parent_freeze_sha256':digest(BASE/'freeze.json'),'phase':'Before recovery-pilot API calls; after first-pilot engineering failures','files':{str(p.relative_to(ROOT)):digest(p) for p in files}})
    print('Frozen recovery pilot: 32 conversations, two development pairs, all actor/gate pilot strata.')

if __name__=='__main__':main()
