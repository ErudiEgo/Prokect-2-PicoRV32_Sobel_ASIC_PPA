"""Capture original topology for the native repair guard; no ODB edits."""
import json
from pathlib import Path
import click
from reader import click_odb
from targeted_diodes import capture_original, encode_original

@click.command()
@click.option('--reference', required=True, type=click.Path())
@click_odb
def main(reader, reference):
    original = capture_original(reader.block)
    Path(reference).write_text(json.dumps(encode_original(original))+'\n')
    print(f'NATIVE TOPOLOGY CAPTURE: {len(original[0])} instances / {len(original[1])} connections')

if __name__ == '__main__':
    main()
