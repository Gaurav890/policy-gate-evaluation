import unittest
from study.analyze_confirmatory import contract_event,ratio,bootstrap
class AnalysisTests(unittest.TestCase):
    def test_contract_exact_and_proxy_denominators(self):
        self.assertFalse(contract_event({'role':'assistant','content':'Hello'}))
        self.assertFalse(contract_event({'role':'assistant','tool_calls':[{}],'content':None}))
        self.assertTrue(contract_event({'role':'assistant','tool_calls':[{},{}],'content':None}))
        self.assertTrue(contract_event({'role':'assistant','tool_calls':[{}],'content':'Working on it'}))
        self.assertFalse(contract_event({'role':'tool','content':'hello'}))
        rows=[{'state':True,'c':True},{'state':True,'c':False},{'state':False,'c':True}]
        self.assertEqual(ratio(rows,lambda r:r['c'],lambda r:r['state']),{'numerator':1,'denominator':2,'rate':.5})
        self.assertIsNone(ratio(rows,lambda r:True,lambda r:False)['rate'])
    def test_cluster_bootstrap_moves_whole_tasks(self):
        rows=[{'domain':'d','task_group':'a','n':True},{'domain':'d','task_group':'a','n':False}]
        result=bootstrap(rows,lambda r:r['n'],lambda r:True,draws=100)
        self.assertEqual(result['low'],.5);self.assertEqual(result['high'],.5)
if __name__=='__main__':unittest.main()
