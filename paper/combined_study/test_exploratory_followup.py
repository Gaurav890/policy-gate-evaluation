"""Check exact-test arithmetic against independent small enumerations."""
import itertools, unittest
from build_exploratory_followup import exact_mcnemar, exact_sign_flip, holm
class ExactTests(unittest.TestCase):
    def test_mcnemar(self):
        self.assertEqual(exact_mcnemar(0,0),1)
        self.assertEqual(exact_mcnemar(3,0),.25)
        self.assertEqual(exact_mcnemar(2,2),1)
        self.assertEqual(exact_mcnemar(0,20),2/2**20)
    def test_sign_flip(self):
        for w in [[],[0,0],[1,2,-1],[2,2,2,-1],[-2,1,0,3]]:
            values=[sum(x*y for x,y in zip(w,signs)) for signs in itertools.product([-1,1],repeat=len(w))]
            expected=sum(abs(v)>=abs(sum(w)) for v in values)/len(values)
            self.assertEqual(exact_sign_flip(w),expected)
    def test_holm(self):
        self.assertEqual(holm([.01,.04,.03,.5]),[.04,.09,.09,.5])
        self.assertEqual(holm([1,1]),[1,1])
if __name__=='__main__':unittest.main()
