import copy,json,tempfile,unittest
from pathlib import Path
from collections import Counter
from unittest.mock import patch
from intervention_study.common import read,save,digest
from intervention_study.compact_study import runner,analyze,collection_pipeline


class CompactTests(unittest.TestCase):
    def test_balanced_fixed_subset_and_exact_imports(self):
        b=runner.BASE;rows=read(b/'allocation.json');parent=read(b.parent/'primary_study/allocation.json')
        expected=[c for c in parent if c['customer']=='scripted' and c['condition']!='oracle' and c['repeat']<2 and int(c['pair_id'].rsplit('-',1)[1]) in [2,3,4,5]]
        self.assertEqual(rows,expected);self.assertEqual(len(rows),1152)
        self.assertEqual(set(Counter(c['pair_id'] for c in rows).values()),{36})
        self.assertEqual(Counter(c['condition'] for c in rows),{'none':384,'broad':384,'decomposed':384})
        imported=read(b/'imports.json')['records'];self.assertEqual(len(imported),102)
        records=[read(b/'episodes'/(ep+'.json')) for ep in imported]
        self.assertEqual(Counter(r['status'] for r in records),{'completed':101,'incomplete':1})
        for r in records:runner.validate_record(r)
        changed=copy.deepcopy(records[0]);changed['status']='different'
        with self.assertRaises(ValueError):runner.validate_record(changed)

    def test_new_records_cannot_claim_the_old_protocol(self):
        b=runner.BASE;imports=read(b/'imports.json')['records']
        cell=next(c for c in read(b/'allocation.json') if c['episode'] not in imports)
        r={**cell,'protocol_sha256':'old'}
        with self.assertRaises(ValueError):runner.validate_record(r)
        r['protocol_sha256']=digest(b/'protocol.json');runner.validate_record(r)

    def test_four_comparisons_keep_missing_attempt_unknown(self):
        b=runner.BASE;rows=read(b/'allocation.json');records=[read(b/'episodes'/(ep+'.json')) for ep in read(b/'imports.json')['records']]
        out=analyze.analyze_data(rows,records,[],cost_by={},dependencies=read(b/'dependencies.json'),customer_checks=[],draws=10)
        self.assertEqual(len(out['primary_contrasts']),4)
        self.assertEqual({e['gate'] for e in out['primary_contrasts']},{'broad','decomposed'})
        for effect in out['primary_contrasts']:
            self.assertEqual(effect['randomization_test']['family_size'],4)
            self.assertIsNone(effect['randomization_test']['p_value'])
        normalized=analyze.make_rows(rows,records,{})
        interrupted=next(r for r in records if r['status']=='incomplete')
        row=next(r for r in normalized if r['episode']==interrupted['episode'])
        self.assertIsNone(row['service_complete']);self.assertEqual(row['outcome_status'],'unresolved')

    def test_first_error_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            with patch.object(runner,'BASE',base):
                runner.retain_stop({'error_type':'TimeoutError'});runner.retain_stop({'error_type':'RuntimeError'})
            self.assertEqual(read(base/'stop.json')['error_type'],'TimeoutError')

    def test_funding_denied_before_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'authorization.json',{'approved':False})
            with self.assertRaises(PermissionError):runner.approved_ceiling(b)

    def test_shadow_only_after_all_live_attempts_and_no_stop(self):
        for complete,stopped in [(False,False),(True,True),(True,False)]:
            with self.subTest(complete=complete,stopped=stopped),tempfile.TemporaryDirectory() as td:
                b=Path(td);cells=[{'episode':'a','condition':'none'},{'episode':'b','condition':'broad'}]
                save(b/'allocation.json',cells);save(b/'episodes/a.json',{'episode':'a','status':'completed'})
                if complete:save(b/'episodes/b.json',{'episode':'b','status':'incomplete'})
                if stopped:save(b/'stop.json',{'error_type':'TimeoutError'})
                save(b/'analysis.json',{'recorded':2 if complete else 1})
                calls=[]
                with patch.object(collection_pipeline,'BASE',b),patch.object(collection_pipeline,'verify'),patch.object(collection_pipeline,'approved_ceiling'),patch.object(collection_pipeline,'command',side_effect=lambda *args:calls.append(args)):
                    collection_pipeline.main()
                self.assertEqual(any('--live' in args for args in calls),complete and not stopped)


if __name__=='__main__':unittest.main()
