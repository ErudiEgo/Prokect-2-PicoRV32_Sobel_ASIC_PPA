"""Installed-API regression checks only. No Step.start, simulation, or PNR."""
import ast
import inspect
import unittest
from openlane.logging import info
from antenna_closure import (AntennaClosure, TargetedDiodes, VerifyAntennaTopology,
                             routing_steps, RepairDesign, RepairTiming, GlobalRouting,
                             CaptureAntennaTopology, NativeAntennaRepair, VerifyNativeTopology)


def missing_self_methods(cls, source):
    tree = ast.parse(source)
    return sorted({n.func.attr for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self'
                   and not callable(getattr(cls, n.func.attr, None))})


class InstalledApiTests(unittest.TestCase):
    def test_no_resizer_after_first_attempt(self):
        self.assertEqual([x[0] for x in routing_steps(0)], [RepairDesign, RepairTiming])
        for iteration in (0, 1, 2):
            self.assertEqual([x[0] for x in routing_steps(iteration, antenna_only=True)], [GlobalRouting])
        for iteration in (1, 2):
            self.assertEqual([x[0] for x in routing_steps(iteration)], [GlobalRouting])

    def test_old_crash_is_detected(self):
        self.assertEqual(missing_self_methods(AntennaClosure, 'self.info("test")'), ['info'])

    def test_every_self_method_exists(self):
        for cls in (AntennaClosure, TargetedDiodes, VerifyAntennaTopology, CaptureAntennaTopology, NativeAntennaRepair, VerifyNativeTopology):
            self.assertEqual(missing_self_methods(cls, inspect.getsource(cls)), [])

    def test_both_info_branches_use_installed_logger(self):
        source = ast.parse(inspect.getsource(AntennaClosure))
        calls = [n for n in ast.walk(source) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'info']
        self.assertEqual(len(calls), 3)
        self.assertTrue(callable(info))
        info('API regression test: logger callable; no physical step executed.')


if __name__ == '__main__':
    unittest.main()
