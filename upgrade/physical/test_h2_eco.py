"""Host-only graph contract tests; these are not RTL simulation or ASIC data."""
import ast
from pathlib import Path
import unittest

p=Path(__file__).parent
source=p/'flow/output_buffer_eco.py'
if not source.exists(): source=p/'h2_targeted_eco.py'
tree=ast.parse(source.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='contraction')
scope={}; exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope)
contract=scope['contraction']


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.old=({'d':'ff','l':'gate','q':'gate'}, {('d','Q'):'a',('l','A'):'a',('q','A'):'b'})
        self.new=({'d':'ff','l':'gate','q':'gate','buf':'buf'},
                  {('d','Q'):'a',('l','A'):'c',('q','A'):'b',('buf','A'):'a',('buf','X'):'c'})
    def test_identity(self): contract(self.old,self.new,['buf'])
    def test_lost_load(self):
        self.new[1][('l','A')]='orphan'
        with self.assertRaises(ValueError): contract(self.old,self.new,['buf'])
    def test_short(self):
        self.new[1][('q','A')]='c'
        with self.assertRaises(ValueError): contract(self.old,self.new,['buf'])
    def test_changed_master(self):
        self.new[0]['d']='different'
        with self.assertRaises(ValueError): contract(self.old,self.new,['buf'])
    def test_deleted_diode_or_extra_cell(self):
        self.new[0]['extra']='diode'
        with self.assertRaises(ValueError): contract(self.old,self.new,['buf'])
    def test_two_branches(self):
        self.old[0]['l2']='gate';self.old[1][('l2','A')]='a'
        self.new[0].update(l2='gate',buf2='buf')
        self.new[1].update({('l2','A'):'e',('buf2','A'):'a',('buf2','X'):'e'})
        contract(self.old,self.new,['buf','buf2'])


if __name__=='__main__': unittest.main()
