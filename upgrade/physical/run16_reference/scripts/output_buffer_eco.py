"""User-run two-driver ECO. --plan-only never mutates the database.

Each original driver feeds A of one non-inverting SKY130 buf_8; X drives
its original net. Every original load and diode stays on that net.
"""
import json
from pathlib import Path
import click
import odb
from reader import click_odb
from targeted_diodes import capture_original, verify_original, encode_original, decode_original

TARGETS = [('_07463_', 'Y', '_02744_'), ('_07515_', 'Y', '_02788_')]
MASTER = 'sky130_fd_sc_hd__buf_8'


def plan(block):
    master = block.getDataBase().findMaster(MASTER)
    if master is None or master.findMTerm('A') is None or master.findMTerm('X') is None:
        raise ValueError('Required SKY130 buffer master/pins unavailable')
    result = []
    for index, (name, pin, net_name) in enumerate(TARGETS):
        inst = block.findInst(name)
        if inst is None or inst.getMaster().getName() != 'sky130_fd_sc_hd__o31ai_4':
            raise ValueError('Unexpected target master: ' + name)
        term = inst.findITerm(pin)
        net = term.getNet()
        if net is None or net.getName() != net_name or net.isSpecial() or str(net.getSigType()) != 'SIGNAL':
            raise ValueError('Unexpected target net: ' + name)
        drivers = [t for t in net.getITerms() if t.isOutputSignal()]
        if len(drivers) != 1 or drivers[0].getInst().getName() != name or list(net.getBTerms()):
            raise ValueError('Expected internal single-driver net')
        new_inst, new_net = f'SOBEL_ECO_BUF_{index}', f'SOBEL_ECO_DRIVER_{index}'
        if block.findInst(new_inst) is not None or block.findNet(new_net) is not None:
            raise ValueError('ECO already present; do not apply twice')
        for pg in ('VPWR', 'VGND', 'VPB', 'VNB'):
            if master.findMTerm(pg) is None: raise ValueError('Buffer PG pin missing')
            if inst.findITerm(pg) is None or inst.findITerm(pg).getNet() is None:
                raise ValueError('Driver power connection missing')
        result.append((inst, term, net, new_inst, new_net))
    return master, result


def positions(block):
    return {i.getName(): [*i.getLocation(), str(i.getOrient())] for i in block.getInsts()}


@click.command()
@click.option('--reference', required=True, type=click.Path())
@click.option('--mode', type=click.Choice(['insert', 'cleanup', 'verify']), default='insert')
@click.option('--plan-only', is_flag=True)
@click_odb
def main(reader, reference, mode, plan_only):
    block = reader.block
    path = Path(reference)
    if mode == 'insert':
        master, targets = plan(block)
        for inst, term, net, new_inst, new_net in targets:
            print('OUTPUT BUFFER PLAN:', inst.getName(), net.getName(), '->', new_inst, MASTER,
                  'preserved loads:', len(list(net.getITerms()))-1)
        for cls, method in [(odb.dbInst, 'create'), (odb.dbNet, 'create'), (odb.dbWire, 'destroy')]:
            if not callable(getattr(cls, method, None)): raise ValueError('Missing ODB API '+method)
        positions(block)  # Read-check location/orientation API before user-run legalization.
        if plan_only:
            print('OUTPUT BUFFER PLAN PASS: 2 drivers; no ODB edits or physical steps')
            return
        if path.exists(): raise FileExistsError(path)
        original = capture_original(block)
        expected = (dict(original[0]), dict(original[1]))
        dirty = []
        for inst, term, net, new_inst, new_net in targets:
            short = odb.dbNet.create(block, new_net)
            short.setSigType('SIGNAL')
            buf = odb.dbInst.create(block, master, new_inst)
            buf.setOrient(inst.getOrient())
            buf.setLocation(*inst.getLocation())
            buf.setPlacementStatus('PLACED')
            term.connect(short)
            buf.findITerm('A').connect(short)
            buf.findITerm('X').connect(net)
            for pg in ('VPWR', 'VGND', 'VPB', 'VNB'):
                buf.findITerm(pg).connect(inst.findITerm(pg).getNet())
            expected[1][(inst.getName(), term.getMTerm().getName())] = new_net
            expected[0][new_inst] = MASTER
            expected[1][(new_inst, 'A')] = new_net
            expected[1][(new_inst, 'X')] = net.getName()
            for pg in ('VPWR', 'VGND', 'VPB', 'VNB'):
                expected[1][(new_inst, pg)] = inst.findITerm(pg).getNet().getName()
            dirty += [net.getName(), new_net]
        # Exact structural identity contract: only two original output net
        # connections changed, each through A->X of one non-inverting buffer.
        verify_original(block, expected)
        if len(list(block.getInsts())) != len(original[0])+2:
            raise ValueError('Unexpected instance additions')
        path.write_text(json.dumps({'expected': encode_original(expected),
            'positions': positions(block), 'dirty_nets': dirty}, indent=2)+'\n')
        print('OUTPUT BUFFER STRUCTURAL CHECK PASS: two identity buffers; all original loads/diodes retained')
    else:
        data = json.loads(path.read_text())
        verify_original(block, decode_original(data['expected']))
        if len(list(block.getInsts())) != len(data['expected']['masters']):
            raise ValueError('Unexpected logic changes after placement/routing')
        if mode == 'verify':
            print('OUTPUT BUFFER ROUTED TOPOLOGY PASS')
            return
        dirty = set(data['dirty_nets'])
        now = positions(block)
        for name, old in data['positions'].items():
            if now[name] != old:
                for t in block.findInst(name).getITerms():
                    if t.getNet() is not None and not t.getNet().isSpecial(): dirty.add(t.getNet().getName())
        if plan_only:
            print('WIRE CLEANUP PLAN:', sorted(dirty)); return
        removed = 0
        for name in sorted(dirty):
            net = block.findNet(name)
            if net is not None and net.getWire() is not None:
                odb.dbWire.destroy(net.getWire()); removed += 1
        Path('wire_cleanup.json').write_text(json.dumps({'dirty_nets': sorted(dirty), 'removed_wires': removed}, indent=2)+'\n')
        print('WIRE CLEANUP:', removed, 'modified/moved nets; other detailed wires retained')


if __name__ == '__main__':
    main()
