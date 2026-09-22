"""Four identity buffers for H2 repair01. Physical edits only in user-run insert.

--plan-only validates the actual checkpoint without modifying its database.
"""
import json
from pathlib import Path
import click
import odb
from reader import click_odb
from targeted_diodes import capture_original, verify_original, encode_original, decode_original

MASTER = 'sky130_fd_sc_hd__buf_8'
PG = ('VPWR', 'VGND', 'VPB', 'VNB')
TARGETS = [('_28558_', 'Y', '_10606_', 'nor4_1'),
           ('_28646_', 'Y', '_10692_', 'nor4_2'),
           ('_37271_', 'Q', r'soc.g_sobel.g_v2.tile_engine.origin\[15\]', 'dfxtp_4')]


def positions(block):
    return {i.getName(): [*i.getLocation(), str(i.getOrient())] for i in block.getInsts()}


def ports(block):
    return {t.getName(): [t.getNet().getName() if t.getNet() else None,
                         str(t.getIoType()), str(t.getSigType())] for t in block.getBTerms()}


def plan(block):
    master = block.getDataBase().findMaster(MASTER)
    if master is None or {t.getName() for t in master.getMTerms()} != {'A', 'X', *PG}:
        raise ValueError('Unexpected buffer master/pins')
    result = []
    for index, (name, pin, netname, cell) in enumerate(TARGETS):
        inst = block.findInst(name)
        if inst is None or inst.getMaster().getName() != 'sky130_fd_sc_hd__'+cell:
            raise ValueError('Wrong driver master: '+name)
        term = inst.findITerm(pin)
        net = term.getNet() if term else None
        if net is None or net.getName() != netname or net.isSpecial() or str(net.getSigType()) != 'SIGNAL':
            raise ValueError('Wrong target net: '+name)
        drivers = [t for t in net.getITerms() if t.isOutputSignal()]
        loads = [t for t in net.getITerms() if str(t.getIoType()) == 'INPUT']
        if len(drivers) != 1 or (drivers[0].getInst().getName(), drivers[0].getMTerm().getName()) != (name, pin) or list(net.getBTerms()) or len(list(net.getITerms())) != len(loads)+1:
            raise ValueError(f'Unexpected net terminals: {name}, drivers={len(drivers)}, loads={len(loads)}, all={len(list(net.getITerms()))}')
        for pg in PG:
            if inst.findITerm(pg) is None or inst.findITerm(pg).getNet() is None:
                raise ValueError('Missing driver PG')
        if index < 2:
            expected_load = [('wire49', 'A'), ('_28649_', 'C')][index]
            if len(loads) != 1 or (loads[0].getInst().getName(), loads[0].getMTerm().getName()) != expected_load:
                raise ValueError('Cap/slew target load changed')
            groups = [[]]
        else:
            logic = {(t.getInst().getName(), t.getMTerm().getName()) for t in loads
                     if t.getInst().getMaster().getName() != 'sky130_fd_sc_hd__diode_2'}
            if len(loads) != 13 or logic != {('fanout9014', 'A'), ('fanout9015', 'A')}:
                raise ValueError('Expected exactly two logic loads and eleven diode_2 inputs')
            # Spatial order, deterministic tie-break. Keep EVERY existing diode.
            loads.sort(key=lambda t: (*t.getInst().getLocation(), t.getInst().getName(), t.getMTerm().getName()))
            groups = [loads[:7], loads[7:]]
        for branch, group in enumerate(groups):
            label = f'H2_ECO_{index}_{branch}'
            if block.findInst(label) or block.findNet(label+'_NET'):
                raise ValueError('ECO already present')
            result.append((inst, term, net, label, group))
    return master, result


def contraction(original, expected, edits):
    """Contract A->X identity edges; original instance/pin/net partition must match."""
    aliases = {}
    def root(n):
        while n in aliases: n = aliases[n]
        return n
    for name in edits:
        a, x = expected[1][(name, 'A')], expected[1][(name, 'X')]
        if root(a) == root(x): raise ValueError('Redundant/cyclic buffer edge')
        aliases[root(a)] = root(x)
    if set(expected[0]) != set(original[0]) | set(edits):
        raise ValueError('Unexpected instance set')
    for name, cell in original[0].items():
        if expected[0][name] != cell: raise ValueError('Original master changed')
    # Compare partitions, not literal new-net names. Prevent shorts between old nets.
    mapped = {}
    for pin, oldnet in original[1].items():
        newnet = root(expected[1][pin])
        if oldnet in mapped and mapped[oldnet] != newnet: raise ValueError('Original net split')
        mapped[oldnet] = newnet
    if len(set(mapped.values())) != len(mapped): raise ValueError('Original nets shorted')


@click.command()
@click.option('--reference', required=True, type=click.Path())
@click.option('--mode', type=click.Choice(['insert', 'cleanup', 'verify']), default='insert')
@click.option('--plan-only', is_flag=True)
@click_odb
def main(reader, reference, mode, plan_only):
    block, path = reader.block, Path(reference)
    if mode == 'insert':
        master, edits = plan(block)
        for inst, term, net, label, group in edits:
            print('H2 ECO PLAN:', label, inst.getName(), net.getName(), 'branch_loads=', len(group))
        positions(block); ports(block)
        for cls, method in [(odb.dbInst, 'create'), (odb.dbNet, 'create'), (odb.dbWire, 'destroy')]:
            if not callable(getattr(cls, method, None)): raise ValueError('Missing ODB API')
        if plan_only:
            print('H2 ECO PLAN PASS: four buffers; fanout branches 7/6; NO DATABASE EDITS')
            return
        if path.exists(): raise FileExistsError(path)
        original = capture_original(block)
        expected = (dict(original[0]), dict(original[1]))
        original_ports, dirty = ports(block), []
        for inst, term, net, label, group in edits:
            new = odb.dbNet.create(block, label+'_NET'); new.setSigType('SIGNAL')
            buf = odb.dbInst.create(block, master, label)
            buf.setOrient(inst.getOrient())
            loc = inst.getLocation() if not group else tuple(sum(t.getInst().getLocation()[k] for t in group)//len(group) for k in (0,1))
            buf.setLocation(*loc); buf.setPlacementStatus('PLACED')
            if group:
                buf.findITerm('A').connect(net); buf.findITerm('X').connect(new)
                for load in group:
                    load.connect(new)
                    expected[1][(load.getInst().getName(), load.getMTerm().getName())] = new.getName()
            else:
                term.connect(new); buf.findITerm('A').connect(new); buf.findITerm('X').connect(net)
                expected[1][(inst.getName(), term.getMTerm().getName())] = new.getName()
            for pg in PG: buf.findITerm(pg).connect(inst.findITerm(pg).getNet())
            expected[0][label] = MASTER
            for t in buf.getITerms(): expected[1][(label, t.getMTerm().getName())] = t.getNet().getName()
            dirty += [net.getName(), new.getName()]
        contraction(original, expected, [e[3] for e in edits])
        verify_original(block, expected)
        if capture_original(block) != expected or ports(block) != original_ports:
            raise ValueError('Unexpected topology/port changes')
        path.write_text(json.dumps({'expected': encode_original(expected), 'original': encode_original(original),
            'ports': original_ports, 'positions': positions(block), 'dirty_nets': dirty}, indent=2)+'\n')
        print('H2 ECO STRUCTURAL PASS: all original cells/diodes retained; identity contraction verified')
    else:
        data = json.loads(path.read_text())
        expected = decode_original(data['expected'])
        verify_original(block, expected)
        if capture_original(block) != expected or ports(block) != data['ports']:
            raise ValueError('Unexpected placement/routing topology changes')
        if mode == 'verify':
            print('H2 ECO ROUTED TOPOLOGY PASS'); return
        dirty = set(data['dirty_nets']); now = positions(block)
        for name, old in data['positions'].items():
            if now[name] != old:
                dirty.update(t.getNet().getName() for t in block.findInst(name).getITerms()
                             if t.getNet() and not t.getNet().isSpecial())
        if plan_only: print('WIRE CLEANUP PLAN:', sorted(dirty)); return
        removed = 0
        for name in sorted(dirty):
            net = block.findNet(name)
            if net and net.getWire(): odb.dbWire.destroy(net.getWire()); removed += 1
        Path('wire_cleanup.json').write_text(json.dumps({'dirty_nets': sorted(dirty), 'removed_wires': removed}, indent=2)+'\n')
        print('WIRE CLEANUP:', removed)


if __name__ == '__main__': main()
