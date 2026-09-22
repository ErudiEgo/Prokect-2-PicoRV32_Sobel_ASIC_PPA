"""Host guard/collector tests. No RTL simulation or physical execution."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import collect_ppa
import ppa


class GuardTests(unittest.TestCase):
    def test_tags(self):
        for bad in ('../run','old_run','s2_../../x','s2_x/y','s2_'):
            with self.assertRaises(ValueError): ppa.tag_check(bad)
        ppa.tag_check('s2_ppa_h2_clk50_01')

    def test_packet_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'source.v').write_text('HOST FIXTURE ONLY')
            ppa.save(root/'READY.json',{'status':'PPA_PAIR_STATIC_PREFLIGHT_PASS','files_sha256':ppa.inventory(root)})
            ppa.verify_packet(root)
            (root/'source.v').write_text('changed')
            with self.assertRaises(ValueError): ppa.verify_packet(root)

    def test_precheck_refuses_existing_directory_before_preparation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'run_inputs/s2_pair_existing').mkdir(parents=True)
            with patch.object(ppa,'ROOT',root), patch.object(ppa,'environment',return_value={}), patch.object(ppa.subprocess,'run') as launch:
                with self.assertRaises(ValueError): ppa.precheck('s2_pair_existing')
                launch.assert_not_called()

    def test_pdk_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'preflight').mkdir();(root/'pdk').mkdir()
            lib=root/'pdk/test.lib';lib.write_text('HOST FIXTURE ONLY')
            ppa.save(root/'preflight/pdk_files_sha256.json',{'/pdk/test.lib':ppa.sha(lib)})
            ppa.verify_pdk(root,{'pdk_root':str(root/'pdk')})
            lib.write_text('changed')
            with self.assertRaises(ValueError): ppa.verify_pdk(root,{'pdk_root':str(root/'pdk')})

    def test_launch_command_and_failure_status_with_mock_only(self):
        with tempfile.TemporaryDirectory(prefix='HOST_LAUNCH_STUB_') as temp:
            root=Path(temp);pair='s2_test_pair';tag='s2_ppa_h1_host_test'
            packet=root/'run_inputs'/pair;(packet/'sources').mkdir(parents=True)
            shutil.copy2(Path(ppa.__file__),packet/'sources/ppa.py')
            env={'pdk_root':str(root/'pdk'),'image_id':ppa.IMAGE}
            ppa.save(packet/'environment.json',env)
            ppa.save(packet/'READY.json',{'status':'PPA_PAIR_STATIC_PREFLIGHT_PASS','files_sha256':ppa.inventory(packet)})
            with patch.object(ppa,'ROOT',root), patch.object(ppa,'environment',return_value=env), patch.object(ppa,'verify_pdk'), patch.object(ppa.subprocess,'run',return_value=SimpleNamespace(returncode=7)) as launch, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ppa.run('h1',tag,pair),7)
                args=launch.call_args.args[0]
                self.assertIn('/design/config_h1.json',args)
                self.assertIn('/design/flow/openlane_with_repairs.py',args)
                self.assertNotIn('--flow',args)
                self.assertNotIn('--from',args)
                self.assertIn(str(root/'run_inputs'/tag)+':/work/run_inputs/'+tag+':ro',args)
                self.assertIn('openlane_exit_status=7',(root/'run_inputs'/tag/'runtime.txt').read_text())
                with self.assertRaises(ValueError):ppa.run('h1',tag,pair)
                self.assertEqual(launch.call_count,1)

    def test_empty_pdk_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'preflight').mkdir()
            ppa.save(root/'preflight/pdk_files_sha256.json',{})
            with self.assertRaises(ValueError):ppa.verify_pdk(root,{'pdk_root':temp})

    def test_incomplete_collection_never_passes_or_loses_corner_fanout(self):
        with tempfile.TemporaryDirectory(prefix='HOST_TEST_NOT_ASIC_') as temp:
            root=Path(temp);tag='s2_host_fixture_only'
            stage=root/'runs'/tag/'1-host-fixture';stage.mkdir(parents=True)
            # Deliberately incomplete host fixture, never research evidence.
            ppa.save(stage/'state_out.json',{'metrics':{'design__max_fanout_violation__count__corner:test':2}})
            with patch.object(collect_ppa,'ROOT',root), contextlib.redirect_stdout(io.StringIO()):
                collect_ppa.collect(tag,export=False)
            result=json.loads(next((root/'reports').glob('*/metrics.json')).read_text())
            self.assertEqual(result['status'],'FAIL_OR_INCOMPLETE')
            self.assertEqual(result['checks']['final_metrics'],'MISSING')
            self.assertEqual(result['checks']['snapshot_and_functional_integrity'],'FAIL')
            self.assertEqual(result['checks']['design__max_fanout_violation__count__corner:test'],'FAIL')


if __name__=='__main__': unittest.main()
