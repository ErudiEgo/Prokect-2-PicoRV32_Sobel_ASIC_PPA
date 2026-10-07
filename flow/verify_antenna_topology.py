"""Read-only topology guard after user-run legalization and routing."""
import json
from pathlib import Path
import click
from reader import click_odb
from targeted_diodes import decode_original, verify_original


@click.command()
@click.option('--reference', required=True, type=click.Path(exists=True))
@click.option('--allow-added-diodes', is_flag=True)
@click.option('--diode-cell')
@click.option('--diode-pin')
@click_odb
def main(reader, reference, allow_added_diodes, diode_cell, diode_pin):
    original = decode_original(json.loads(Path(reference).read_text()))
    verify_original(reader.block, original)
    current = {i.getName(): i for i in reader.block.getInsts()}
    added = set(current) - set(original[0])
    if added and not allow_added_diodes:
        raise ValueError('Antenna-only routing added instances')
    if allow_added_diodes:
        if not diode_cell or not diode_pin: raise ValueError('Missing configured diode cell/pin')
        for name in added:
            inst = current[name]
            term = inst.findITerm(diode_pin)
            if inst.getMaster().getName() != diode_cell or term is None or term.getNet() is None:
                raise ValueError('Native antenna repair added non-diode or disconnected instance: '+name)
        print(f'NATIVE ADDED DIODE CHECK: {len(added)} connected PDK diodes; original logic preserved')
    print(f'ANTENNA TOPOLOGY PASS: {len(original[0])} instances; '
          f'{len(original[1])} connections unchanged, including diode signal pins')


if __name__ == '__main__':
    main()
