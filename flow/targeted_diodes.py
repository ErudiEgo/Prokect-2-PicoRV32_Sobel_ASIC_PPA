"""User-flow ODB edit; --plan-only reads/validates targets without changing ODB.

Uses the installed OpenLane 2.3.10 DiodeInserter (Apache-2.0, Efabless /
Sylvain Munaut) for placement next to the reported gate, not its net-wide scan.
"""
import json
from pathlib import Path
import click
import odb
from reader import click_odb
from diodes import DiodeInserter
from antenna_targets import canonical


def capture_original(block):
    """Use exact ODB names; dbNet.getId is absent in the pinned Python API."""
    masters = {}
    connections = {}
    for inst in block.getInsts():
        name = inst.getName()
        if name in masters: raise ValueError('Duplicate original instance name')
        masters[name] = inst.getMaster().getName()
        for term in inst.getITerms():
            net = term.getNet()
            connections[(name, term.getMTerm().getName())] = net.getName() if net is not None else None
    return masters, connections


def verify_original(block, original):
    masters, connections = original
    for name, master in masters.items():
        inst = block.findInst(name)
        if inst is None or inst.getMaster().getName() != master:
            raise ValueError('Original logic instance changed during diode edit: '+name)
    for (name, pin), net_name in connections.items():
        term = block.findInst(name).findITerm(pin)
        if term is None: raise ValueError('Original terminal disappeared')
        net = term.getNet()
        if (net.getName() if net is not None else None) != net_name:
            raise ValueError('Original connectivity changed during diode edit: '+name+'/'+pin)


def encode_original(original):
    masters, connections = original
    return {'masters': masters,
            'connections': [[name, pin, net] for (name, pin), net in connections.items()]}


def decode_original(data):
    return data['masters'], {(name, pin): net for name, pin, net in data['connections']}


def resolve_targets(block, rows):
    instances = {}
    for inst in block.getInsts():
        name = canonical(inst.getName())
        if name in instances: raise ValueError("Ambiguous canonical instance name: " + name)
        instances[name] = inst
    targets = []
    seen = set()
    for row in rows:
        inst_name, pin = canonical(row['pin']).rsplit('/', 1)
        inst = instances.get(inst_name)
        term = inst.findITerm(pin) if inst else None
        if term is None or term.getNet() is None:
            raise ValueError("Antenna target pin not connected: " + row['pin'])
        net = term.getNet()
        if canonical(net.getName()) != canonical(row['net']):
            raise ValueError("Antenna target net changed: " + row['pin'])
        if term.isOutputSignal() or net.isSpecial() or 'diode' in inst.getMaster().getName():
            raise ValueError("Expected a gate input, not driver/diode/special net: " + row['pin'])
        key = (inst_name, pin)
        if key in seen: raise ValueError("Duplicate target pin")
        seen.add(key)
        targets.append((row, net, term))
    return targets


@click.command()
@click.option('--targets', required=True, type=click.Path(exists=True))
@click.option('--diode-cell', required=True)
@click.option('--diode-pin', required=True)
@click.option('--plan-only', is_flag=True)
@click_odb
def main(reader, targets, diode_cell, diode_pin, plan_only):
    rows = json.loads(Path(targets).read_text())
    resolved = resolve_targets(reader.block, rows)
    master = reader.block.getDataBase().findMaster(diode_cell)
    if master is None or master.findMTerm(diode_pin) is None:
        raise ValueError("Configured PDK diode cell/pin is missing")
    if not callable(getattr(odb.dbWire, 'destroy', None)):
        raise ValueError('Installed ODB API lacks dbWire.destroy')
    for row, net, term in resolved:
        print('TARGET', json.dumps(row), 'ODB_PIN', term.getInst().getName()+'/'+term.getMTerm().getName())
    original = capture_original(reader.block)
    verify_original(reader.block, original)
    print(f'CONNECTIVITY READ CHECK: {len(original[0])} instances / {len(original[1])} terminals verified using exact net names')
    if plan_only:
        print(f'TARGET PLAN PASS: {len(resolved)} pins resolved; no ODB changes')
        return
    if not resolved: raise ValueError('No targets supplied to physical diode edit')
    # Validate every target BEFORE the first edit. No original logic instance
    # is removed or reconnected. Old detailed wires must not survive relocation.
    di = DiodeInserter(reader, diode_cell, diode_pin, 0, side_strategy='pin')
    for row, net, term in resolved:
        di.insert_diode(net, term, di.net_source(net))
    verify_original(reader.block, original)
    after = {i.getName() for i in reader.block.getInsts()}
    if len(after - original[0].keys()) != len(resolved):
        raise ValueError('Inserted diode count does not match unique target pins')
    # Preserve logic and diode signal connectivity through later routing.
    # New diode power pins are connected by standard OpenLane global-connect.
    guarded = capture_original(reader.block)
    added = after - original[0].keys()
    guarded = (guarded[0], {key: net for key, net in guarded[1].items()
                           if key[0] not in added or key[1] == diode_pin})
    Path(targets).with_name('topology_after_diodes.json').write_text(
        json.dumps(encode_original(guarded)) + '\n')
    for net in reader.block.getNets():
        wire = net.getWire()
        if wire is not None: odb.dbWire.destroy(wire)
    print(f'TARGETED DIODE EDIT: inserted {len(resolved)}; original logic/connectivity preserved; detailed wires cleared for rerouting')


if __name__ == '__main__':
    main()
