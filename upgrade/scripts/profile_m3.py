"""Validate measured counters and derive explicitly scoped metrics; no simulation."""
import csv
import json
from pathlib import Path


def expected_v1_reads(width, height, channels):
    if min(width, height) < 1 or channels not in (1, 3):
        raise ValueError('Invalid dimensions/channels')
    # Every in-bounds neighbour is fetched once per output sample in DMA v1.
    return channels * (4*(width-1)*(height-1) + 2*height*(width-1) + 2*width*(height-1))


def expected_reads(w,h,c,t,mode):
    if mode==0: return 0
    if mode==1: return expected_v1_reads(w,h,c)
    if mode!=3: raise ValueError('Invalid profiling mode')
    return c*sum((min(w,x+t+1)-max(0,x-1))*(min(h,y+t+1)-max(0,y-1))
                 for y in range(0,h,t) for x in range(0,w,t))


def validate_profile(p, execution, mode):
    if p.get('schema') != 2 or p.get('scope') != 'testbench_only':
        raise ValueError('Stage2 requires measured profile schema 2')
    counters = (
        'cycles cpu_idle_cycles cpu_fetch_cycles cpu_mmio_cycles cpu_data_cycles '
        'cpu_wait_cycles dma_wait_cycles tile_busy_cycles cpu_fetch_tx '
        'cpu_data_read_tx cpu_data_write_tx mmio_read_tx mmio_write_tx '
        'tile_start_tx tile_status_tx dma_read_tx dma_write_tx '
        'ext_idle_cycles ext_wait_cycles ext_accept_cycles '
        'ext_read_tx ext_write_tx ext_ram_read_tx ext_ram_write_tx '
        'ext_host_write_tx ext_ram_write_bytes dma_arb_wait_cycles '
        'dma_service_wait_cycles cpu_external_arb_wait_cycles '
        'cpu_external_service_wait_cycles cpu_mmio_wait_cycles '
        'cpu_image_read_tx dma_image_read_tx output_write_tx output_write_bytes'
    ).split()
    for key in counters:
        if type(p.get(key)) is not int or p[key] < 0:
            raise ValueError(f'Invalid/missing measured counter: {key}')
    def same(a, b, label):
        if a != b:
            raise ValueError(f'Profile {label}: {a} != {b}')
    same(p['cycles'], execution['cycles'], 'execution interval')
    same(p['cycles'], sum(p[k] for k in ('cpu_idle_cycles','cpu_fetch_cycles','cpu_mmio_cycles','cpu_data_cycles')), 'CPU partition')
    same(p['cycles'], sum(p[k] for k in ('ext_idle_cycles','ext_wait_cycles','ext_accept_cycles')), 'external bus partition')
    same(p['ext_accept_cycles'], p['ext_read_tx'] + p['ext_write_tx'], 'external transactions')
    same(p['ext_read_tx'], p['cpu_fetch_tx'] + p['cpu_data_read_tx'] + p['dma_read_tx'], 'read ownership')
    same(p['ext_write_tx'], p['cpu_data_write_tx'] + p['dma_write_tx'], 'write ownership')
    same(p['ext_read_tx'], p['ext_ram_read_tx'], 'RAM reads')
    same(p['ext_write_tx'], p['ext_ram_write_tx'] + p['ext_host_write_tx'], 'RAM/host writes')
    same(p['dma_wait_cycles'], p['dma_arb_wait_cycles'] + p['dma_service_wait_cycles'], 'DMA waits')
    same(p['cpu_wait_cycles'], p['cpu_external_arb_wait_cycles'] + p['cpu_external_service_wait_cycles'] + p['cpu_mmio_wait_cycles'], 'CPU waits')
    w,h,c,t = (execution[k] for k in ('width','height','channels','tile'))
    samples = w*h*c
    same(p['output_write_bytes'], samples, 'output bytes')
    same(p['output_write_tx'], samples, 'byte output transactions')
    same(p['dma_image_read_tx'], p['dma_read_tx'], 'DMA input range')
    same(p['dma_write_tx'], samples if mode else 0, 'DMA writes')
    same(p['dma_read_tx'], expected_reads(w,h,c,t,mode), 'analytical architecture read count')
    same(p['tile_start_tx'], ((w+t-1)//t)*((h+t-1)//t)*c if mode else 0, 'tile starts')
    for key in ('cpu_wait_cycles','dma_wait_cycles','tile_busy_cycles'):
        if p[key] > p['cycles']:
            raise ValueError(f'{key} exceeds observation interval')
    if not p['ext_ram_write_tx'] <= p['ext_ram_write_bytes'] <= 4*p['ext_ram_write_tx']:
        raise ValueError('RAM byte strobes inconsistent')
    return p


def derive_metrics(directory, execution, mode):
    directory = Path(directory)
    p = validate_profile(json.loads((directory/'profile.json').read_text()), execution, mode)
    with (directory/'tiles.csv').open(newline='') as stream:
        events = list(csv.DictReader(stream))
    if not events:
        raise ValueError('No measured region completion')
    first = int(events[0]['cycle']) - execution['start_cycle']
    last = int(events[-1]['cycle']) - execution['start_cycle']
    if not 0 < first <= last < execution['cycles']:
        raise ValueError('Invalid region completion interval')
    pixels = execution['width']*execution['height']
    samples = pixels*execution['channels']
    return {
        'status': 'DERIVED_FROM_VERIFIED_RTL_COUNTERS',
        'cycles_per_spatial_pixel': p['cycles']/pixels,
        'cycles_per_channel_sample': p['cycles']/samples,
        'first_region_cycles': first, 'last_region_cycles': last,
        'external_read_bus_bytes': 4*p['ext_read_tx'],
        'external_ram_written_bytes': p['ext_ram_write_bytes'],
        'dma_read_bus_bytes': 4*p['dma_read_tx'],
        'dma_read_transactions_per_sample': p['dma_read_tx']/samples,
        'cpu_image_read_transactions_per_sample': p['cpu_image_read_tx']/samples,
        'external_bus_wait_fraction': p['ext_wait_cycles']/p['cycles'],
        'dma_arbitration_wait_cycles': p['dma_arb_wait_cycles'],
        'dma_service_wait_cycles': p['dma_service_wait_cycles'],
        'analytical_expected_dma_read_tx': expected_reads(execution['width'],execution['height'],execution['channels'],execution['tile'],mode),
        'notes': [
            'Read bus bytes count full 32-bit responses; not unique/useful pixel bytes.',
            'Service wait means granted but not acknowledged, including synchronous handshake latency.',
            'Arbitration wait includes owner-selection/release bubbles and contention; not contention alone.',
            'CPU/DMA busy/wait counters overlap; do not add them to form total cycles.',
            'S1 firmware is unchanged; compare within the declared DMA_VERSION and memory condition.',
            'No clock-derived FPS, ASIC power, or energy is claimed.'
        ]
    }
