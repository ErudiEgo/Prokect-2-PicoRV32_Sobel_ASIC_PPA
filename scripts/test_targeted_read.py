"""Read-only ODB regression. Changes expected Python data, never the database."""
import sys
import json
from pathlib import Path
from reader import OdbReader
from targeted_diodes import capture_original, verify_original, encode_original, decode_original

reader = OdbReader(sys.argv[1])
original = capture_original(reader.block)
verify_original(reader.block, original)
assert decode_original(json.loads(json.dumps(encode_original(original)))) == original
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(json.dumps(encode_original(original)))
    for kind, want_diode in (('diode', True), ('logic', False)):
        name = next(n for n, m in original[0].items() if ('__diode_' in m) == want_diode)
        reduced = ({n:m for n,m in original[0].items() if n != name},
                   {k:v for k,v in original[1].items() if k[0] != name})
        Path(sys.argv[2]).with_name('topology_without_'+kind+'.json').write_text(json.dumps(encode_original(reduced)))

masters, connections = original
if not masters or not connections: raise AssertionError('Expected real SoC checkpoint')

bad_masters = dict(masters)
bad_masters[next(iter(masters))] = '__UNIT_TEST_WRONG_MASTER__'
try:
    verify_original(reader.block, (bad_masters, connections))
except ValueError:
    pass
else:
    raise AssertionError('Master mismatch was not detected')

bad_connections = dict(connections)
bad_connections[next(iter(connections))] = '__UNIT_TEST_WRONG_NET__'
try:
    verify_original(reader.block, (masters, bad_connections))
except ValueError:
    pass
else:
    raise AssertionError('Connection mismatch was not detected')
verify_original(reader.block, original)
print(f'ODB READ REGRESSION PASS: {len(masters)} instances / {len(connections)} terminals; both mismatch guards work; no ODB edit.')
