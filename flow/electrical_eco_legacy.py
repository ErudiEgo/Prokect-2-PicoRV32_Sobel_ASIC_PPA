"""Bounded source-isolation/repeater-tree ECO. Only the user runs real edits.

Distances bound proposed placement geometry, not extracted capacitance or delay.
All existing instances are locked for legalization, then their statuses restored.
"""
import json
import math
import itertools
from pathlib import Path
import odb
from targeted_diodes import capture_original, verify_original, encode_original, decode_original

MASTER = 'sky130_fd_sc_hd__buf_8'
ROOT_MASTER = 'sky130_fd_sc_hd__buf_2'
PG = ('VPWR', 'VGND', 'VPB', 'VNB')
EDGE_UM = 80
LEAF_SUM_UM = 60
ROOT_AFTER_UM = 25
NET_SUM_AFTER_UM = 240
MAX_BUFFERS = 1600


def pinname(t):
    return t.getInst().getName() + '/' + t.getMTerm().getName()


def term(block, name):
    inst, pin = name.rsplit('/', 1)
    obj = block.findInst(inst)
    if obj is None or obj.findITerm(pin) is None:
        raise ValueError('Missing pin ' + name)
    return obj.findITerm(pin)


def positions(block):
    return {i.getName(): [*i.getLocation(), str(i.getOrient())] for i in block.getInsts()}


def bterms(block):
    return {t.getName(): t.getNet().getName() if t.getNet() else None for t in block.getBTerms()}


def distance(a, b):
    return sum(abs(x-y) for x, y in zip(a, b))


def partition(items):
    span = [max(x['xy'][a] for x in items)-min(x['xy'][a] for x in items) for a in (0, 1)]
    axis = 0 if span[0] >= span[1] else 1
    ordered = sorted(items, key=lambda x: (x['xy'][axis], x['xy'][1-axis], x['pin']))
    half = len(ordered)//2
    if not half:
        raise ValueError('Cannot split singleton')
    return [ordered[:half], ordered[half:]]


def tree(loads, origin, name, index, dbu):
    nodes = []

    def add(upstream, xy, master=MASTER):
        node = dict(buffer=f'H3_ECO17_B_{index}_{len(nodes)}',
                    net=f'H3_ECO17_N_{index}_{len(nodes)}', upstream=upstream,
                    master=master, xy=list(xy), loads=[])
        nodes.append(node)
        return node

    root = add(name, origin, ROOT_MASTER)

    def branch(parent, items):
        center = [sum(x['xy'][a] for x in items)//len(items) for a in (0, 1)]
        start = parent['xy']
        count = max(1, math.ceil(distance(start, center)/(EDGE_UM*dbu)))
        for k in range(1, count+1):
            xy = [start[a] + (center[a]-start[a])*k//count for a in (0, 1)]
            parent = add(parent['net'], xy)
        total = sum(distance(center, item['xy']) for item in items)
        if len(items) <= 3 and total <= LEAF_SUM_UM*dbu:
            parent['loads'] = sorted(x['pin'] for x in items)
        else:
            for group in partition(items):
                branch(parent, group)

    branch(root, loads)
    return nodes


def validate_tree(row, original_loads):
    seen = {row['net']}
    buffers = set()
    covered = list(row.get("retained_loads", []))
    fanout = {row['net']: len(row.get('retained_loads', []))}
    for node in row['branches']:
        if node['upstream'] not in seen or node['net'] in seen or node['buffer'] in buffers:
            raise ValueError('Cycle, duplicate or disconnected tree')
        if node['master'] not in (MASTER, ROOT_MASTER):
            raise ValueError('Non-identity cell requested')
        seen.add(node['net']); buffers.add(node['buffer'])
        fanout[node['upstream']] += 1
        fanout[node['net']] = len(node['loads'])
        covered.extend(node['loads'])
    if sorted(covered) != sorted(original_loads) or len(set(covered)) != len(covered):
        raise ValueError('Lost or duplicated original load')
    if fanout[row['net']] != (10 if row.get('retained_loads') else 1) or any(v > 3 for k,v in fanout.items() if k != row['net']):
        raise ValueError('Fanout planning bound exceeded')


def plan(block, pins):
    dbu = block.getDbUnitsPerMicron()
    for master_name in (MASTER, ROOT_MASTER):
        master = block.getDataBase().findMaster(master_name)
        if master is None or any(master.findMTerm(p) is None for p in ('A', 'X', *PG)):
            raise ValueError('Missing master/pins ' + master_name)
        if str(master.findMTerm('A').getIoType()) != 'INPUT' or str(master.findMTerm('X').getIoType()) != 'OUTPUT':
            raise ValueError('Invalid buffer directions')
    nets = {}
    for name in pins:
        t = term(block, name)
        net = t.getNet()
        if net is None or not t.isOutputSignal():
            raise ValueError('Target is not a connected driver: ' + name)
        nets[net.getName()] = net
    result = []
    for index, (name, net) in enumerate(sorted(nets.items())):
        drivers = [t for t in net.getITerms() if t.isOutputSignal()]
        if net.isSpecial() or str(net.getSigType()) != 'SIGNAL' or list(net.getBTerms()) or len(drivers) != 1:
            raise ValueError('Target not an internal single-driver signal: ' + name)
        driver = drivers[0]
        loads = [t for t in net.getITerms() if not t.isOutputSignal()]
        if not loads or len(loads) > 24:
            raise ValueError('Unexpected load count ' + name)
        for t in loads:
            io = str(t.getIoType())
            if io != 'INPUT' and not (io == 'INOUT' and 'diode' in t.getInst().getMaster().getName()):
                raise ValueError('Unsupported sink ' + pinname(t))
        power = {}
        for pg in PG:
            t = driver.getInst().findITerm(pg)
            if t is None or t.getNet() is None:
                raise ValueError('Missing PG ' + name)
            power[pg] = t.getNet().getName()
        items = [dict(pin=pinname(t), xy=list(t.getInst().getLocation())) for t in loads]
        selected = items
        origin = list(driver.getInst().getLocation())
        retained = []
        if pinname(driver) == 'fanout1278/X':
            # Keep every existing antenna diode on its protected original net.
            # Move four geographically clustered logic inputs behind one branch.
            logic = [i for i in items if 'diode' not in term(block,i['pin']).getInst().getMaster().getName()]
            if len(items) != 13 or len(logic) != 8:
                raise ValueError('Unexpected fanout1278 inventory')
            def score(group):
                span = sum(max(i['xy'][a] for i in group)-min(i['xy'][a] for i in group) for a in (0,1))
                return span, tuple(sorted(i['pin'] for i in group))
            selected = list(min(itertools.combinations(logic,4), key=score))
            origin = [sorted(i['xy'][a] for i in selected)[1] for a in (0,1)]
            retained = sorted(i['pin'] for i in items if i not in selected)
        row = dict(net=name, driver=pinname(driver), driver_cell=driver.getInst().getMaster().getName(),
                   power=power, branches=tree(selected, origin, name, index, dbu))
        if retained:
            row['retained_loads'] = retained
            row['root_anchor'] = origin
            row['root_search_um'] = 80
            row['split_scope'] = 'Load-side branch; original net has nine retained loads plus one buffer input; extracted cap/timing require actual reports.'
        validate_tree(row, [i['pin'] for i in items])
        for node in row['branches']:
            if block.findInst(node['buffer']) or block.findNet(node['net']):
                raise ValueError('ECO already applied')
        result.append(row)
    if sum(len(r['branches']) for r in result) > MAX_BUFFERS:
        raise ValueError('Bounded ECO buffer budget exceeded')
    return result


def check_legalized_geometry(block, rows):
    dbu = block.getDbUnitsPerMicron()
    for row in rows:
        root = row['branches'][0]
        driver_xy = row.get('root_anchor', term(block, row['driver']).getInst().getLocation())
        root_xy = block.findInst(root['buffer']).getLocation()
        if distance(driver_xy, root_xy) > row.get('root_search_um', ROOT_AFTER_UM)*dbu:
            raise ValueError('Source isolation buffer moved too far: ' + row['driver'])
        for node in row['branches']:
            xy = block.findInst(node['buffer']).getLocation()
            net = block.findNet(node['net'])
            sinks = [t for t in net.getITerms() if not t.isOutputSignal()]
            if len(sinks) > 3 or sum(distance(xy, t.getInst().getLocation()) for t in sinks) > NET_SUM_AFTER_UM*dbu:
                raise ValueError('Legalization broke the bounded tree: ' + node['net'])


def run(block, mode, reference, plan_file, pins_file, plan_only=False):
    ref = Path(reference)
    if mode == 'insert':
        rows = plan(block, json.loads(Path(pins_file).read_text()))
        if rows != json.loads(Path(plan_file).read_text()):
            raise ValueError('Frozen plan does not match checkpoint')
        count = sum(len(r['branches']) for r in rows)
        if plan_only:
            print('ECO PLAN PASS', len(rows), 'nets', count, 'buffers; no physical edit')
            return
        if ref.exists():
            raise FileExistsError(ref)
        original = capture_original(block)
        expected = (dict(original[0]), dict(original[1]))
        old_positions = positions(block)
        statuses = {i.getName(): str(i.getPlacementStatus()) for i in block.getInsts()}
        ports = bterms(block)
        for i in block.getInsts():
            i.setPlacementStatus('LOCKED')
            if not i.isFixed():
                raise ValueError('Original instance did not lock: ' + i.getName())
        dirty = []
        for row in rows:
            dirty.append(row['net'])
            for node in row['branches']:
                net = odb.dbNet.create(block, node['net']); net.setSigType('SIGNAL')
                buf = odb.dbInst.create(block, block.getDataBase().findMaster(node['master']), node['buffer'])
                buf.setOrient('R0'); buf.setLocation(*node['xy']); buf.setPlacementStatus('PLACED')
                buf.findITerm('A').connect(block.findNet(node['upstream']))
                buf.findITerm('X').connect(net)
                expected[0][node['buffer']] = node['master']
                expected[1][(node['buffer'], 'A')] = node['upstream']
                expected[1][(node['buffer'], 'X')] = node['net']
                for pg, power_net in row['power'].items():
                    buf.findITerm(pg).connect(block.findNet(power_net))
                    expected[1][(node['buffer'], pg)] = power_net
                for pin in node['loads']:
                    term(block, pin).connect(net)
                    inst, port = pin.rsplit('/', 1)
                    expected[1][(inst, port)] = node['net']
                dirty.append(node['net'])
        verify_original(block, expected)
        if bterms(block) != ports or len(list(block.getInsts())) != len(expected[0]):
            raise ValueError('Unexpected instance/port change')
        ref.write_text(json.dumps(dict(expected=encode_original(expected), ports=ports,
                        positions=old_positions, statuses=statuses, dirty_nets=dirty, rows=rows), indent=2))
        print('ECO STRUCTURAL CHECK PASS:', count, 'identity buffers; original instances locked')
        return
    data = json.loads(ref.read_text())
    verify_original(block, decode_original(data['expected']))
    if bterms(block) != data['ports'] or len(list(block.getInsts())) != len(data['expected']['masters']):
        raise ValueError('Unexpected topology change')
    now = positions(block)
    if any(now[name] != xy for name, xy in data['positions'].items()):
        raise ValueError('Legalization moved an original instance; stop before routing')
    check_legalized_geometry(block, data['rows'])
    if mode == 'verify':
        print('ECO ROUTED TOPOLOGY PASS; original placement unchanged')
        return
    if plan_only:
        print('CLEANUP PLAN', len(data['dirty_nets'])); return
    for name, status in data['statuses'].items():
        block.findInst(name).setPlacementStatus(status)
    for name in data['dirty_nets']:
        net = block.findNet(name)
        if net.getWire() is not None:
            odb.dbWire.destroy(net.getWire())
        net.clearGuides()
        if list(net.getGuides()):
            raise ValueError('Stale route guide remains')
    print('ECO invalidated routing for', len(data['dirty_nets']), 'target/new nets; original placements restored')
