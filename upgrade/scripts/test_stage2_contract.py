"""Host-only negative checker tests. Synthetic counters are never RTL evidence."""
import copy
import unittest
from profile_contract import expected_v1_reads, validate_profile


class ContractTests(unittest.TestCase):
    def test_read_formula_against_neighbour_enumeration(self):
        for w,h in ((1,1),(1,7),(9,1),(2,2),(17,19),(32,32),(37,35)):
            n=sum(0<=x+dx<w and 0<=y+dy<h
                  for y in range(h) for x in range(w)
                  for dy in (-1,0,1) for dx in (-1,0,1) if (dx,dy)!=(0,0))
            for c in (1,3):
                self.assertEqual(expected_v1_reads(w,h,c),c*n)

    def fixture(self):
        p=dict(schema=2,scope='testbench_only',cycles=100,
               cpu_idle_cycles=30,cpu_fetch_cycles=40,cpu_mmio_cycles=20,cpu_data_cycles=10,
               cpu_wait_cycles=20,dma_wait_cycles=7,tile_busy_cycles=50,
               cpu_fetch_tx=10,cpu_data_read_tx=2,cpu_data_write_tx=2,
               mmio_read_tx=3,mmio_write_tx=6,tile_start_tx=1,tile_status_tx=3,
               dma_read_tx=12,dma_write_tx=4,ext_idle_cycles=40,ext_wait_cycles=30,
               ext_accept_cycles=30,ext_read_tx=24,ext_write_tx=6,
               ext_ram_read_tx=24,ext_ram_write_tx=5,ext_host_write_tx=1,
               ext_ram_write_bytes=8,dma_arb_wait_cycles=3,dma_service_wait_cycles=4,
               cpu_external_arb_wait_cycles=4,cpu_external_service_wait_cycles=10,
               cpu_mmio_wait_cycles=6,cpu_image_read_tx=0,dma_image_read_tx=12,
               output_write_tx=4,output_write_bytes=4)
        e=dict(cycles=100,width=2,height=2,channels=1,tile=16)
        return p,e

    def test_consistent_synthetic_fixture(self):
        p,e=self.fixture()
        self.assertEqual(validate_profile(p,e,1),p)

    def test_valid_software_partition(self):
        p,e=self.fixture()
        p.update(dma_read_tx=0,dma_write_tx=0,dma_image_read_tx=0,tile_start_tx=0,
                 dma_wait_cycles=0,dma_arb_wait_cycles=0,dma_service_wait_cycles=0,
                 tile_busy_cycles=0,cpu_data_write_tx=6,cpu_image_read_tx=2,
                 ext_read_tx=12,ext_ram_read_tx=12,ext_accept_cycles=18,ext_idle_cycles=52)
        self.assertEqual(validate_profile(p,e,0),p)

    def test_corrupt_counters_rejected(self):
        p,e=self.fixture()
        for key in ('cycles','ext_accept_cycles','dma_read_tx','dma_image_read_tx',
                    'output_write_bytes','tile_start_tx','cpu_wait_cycles',
                    'dma_service_wait_cycles','ext_host_write_tx'):
            with self.subTest(key=key):
                bad=copy.deepcopy(p);bad[key]+=1
                with self.assertRaises(ValueError): validate_profile(bad,e,1)
        for value in (-1,True,0.5,None):
            bad=copy.deepcopy(p);bad['cpu_image_read_tx']=value
            with self.assertRaises(ValueError): validate_profile(bad,e,1)

    def test_software_must_not_use_dma(self):
        p,e=self.fixture()
        with self.assertRaises(ValueError): validate_profile(p,e,0)


if __name__=='__main__':
    unittest.main()
