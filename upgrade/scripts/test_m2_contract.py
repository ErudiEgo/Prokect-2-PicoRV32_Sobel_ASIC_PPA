"""Host-only validation tests; mock execution records are not RTL evidence."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from s1_firmware import validate_s1
from run_m2_tests import measure

ROOT=Path(__file__).resolve().parents[1]

class M2ContractTests(unittest.TestCase):
    def test_s1_frozen_sources_and_binary_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            shutil.copytree(ROOT/'firmware',root/'firmware')
            validate_s1(root)
            header=root/'firmware/s1/sobel_s1.h'
            old=header.read_bytes();header.write_bytes(old+b'\n/* changed */\n')
            with self.assertRaisesRegex(ValueError,'Stale S1'): validate_s1(root)
            header.write_bytes(old)
            image=root/'firmware/s1/generated/s1.hex'
            data=image.read_bytes();image.write_bytes(b'ff'+data[2:])
            with self.assertRaisesRegex(ValueError,'Invalid S1 HEX'): validate_s1(root)

    def test_s1_is_software_despite_nonzero_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'profile.json').write_text(json.dumps({'mmio_read_tx':0,'mmio_write_tx':0,'tile_busy_cycles':0}))
            with patch('run_m2_tests.verify_mode',return_value={'hardware_enable_sobel':1}), \
                 patch('run_m2_tests.derive_metrics',return_value={'notes':[]}) as derive:
                measure(root,2,{'tile':16,'memory_wait':1},{'width':2,'height':2},b'')
                self.assertEqual(derive.call_args.args[2],0)

    def test_wrong_hardware_and_software_mmio_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'profile.json').write_text(json.dumps({'mmio_read_tx':1,'mmio_write_tx':0,'tile_busy_cycles':0}))
            cfg={'tile':16,'memory_wait':1};meta={'width':2,'height':2}
            with patch('run_m2_tests.verify_mode',return_value={'hardware_enable_sobel':0}):
                with self.assertRaisesRegex(ValueError,'same accelerator-present'):
                    measure(root,0,cfg,meta,b'')
            with patch('run_m2_tests.verify_mode',return_value={'hardware_enable_sobel':1}), \
                 patch('run_m2_tests.derive_metrics',return_value={'notes':[]}):
                with self.assertRaisesRegex(ValueError,'unexpectedly used'):
                    measure(root,2,cfg,meta,b'')

if __name__=='__main__': unittest.main()
