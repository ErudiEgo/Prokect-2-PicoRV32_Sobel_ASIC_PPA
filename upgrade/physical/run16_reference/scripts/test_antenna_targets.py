"""Parser unit tests, not RTL simulation or physical results.

Optional argument: a real antenna.rpt from repair_03 for the 6-net/7-pin audit.
"""
import sys
import unittest
from pathlib import Path
from antenna_targets import checked_targets


class ParserTests(unittest.TestCase):
    def test_same_pin_two_layers_is_one_target(self):
        # Artificial parser fixture only, never used as project run evidence.
        text = 'Net: bus\\[0\\]\n Pin: gate/A\n Layer: met3\n Required ratio: 400 (VIOLATED)\n Layer: via3\n Required ratio: 6 (VIOLATED)\n'
        rows = checked_targets(text, 1, 1)
        self.assertEqual(rows[0]['layers'], ['met3', 'via3'])

    def test_truncated_or_missing_report_cannot_look_clean(self):
        with self.assertRaises(ValueError): checked_targets('', 6, 7)
        with self.assertRaises(ValueError): checked_targets('VIOLATED\n', 1, 1)

    def test_clean_report_requires_zero_metrics(self):
        self.assertEqual(checked_targets('', 0, 0), [])


if __name__ == '__main__':
    if len(sys.argv) > 1:
        report = Path(sys.argv.pop(1))
        rows = checked_targets(report.read_text(encoding='utf-8'), 6, 7)
        expected = {'fanout1541/A', '_07123_/A1', 'fanout901/A', 'fanout865/A',
                    'fanout866/A', 'fanout2599/A', 'fanout2264/A'}
        assert {r['pin'] for r in rows} == expected
        print('REAL REPORT PARSER CHECK: repair_03, 6 nets / 7 unique pins; no flow executed')
    unittest.main()
