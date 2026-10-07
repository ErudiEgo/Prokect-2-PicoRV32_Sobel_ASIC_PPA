"""Check both inserted identity-buffer functions in every resolved Liberty."""
import gzip
import json
from pathlib import Path
import re

config = json.loads(Path('/audit/resolved.json').read_text())
checked = []
for filename in sorted({str(p) for group in config['LIB'].values() for p in group}):
    opener = gzip.open if filename.endswith('.gz') else open
    with opener(filename, 'rt') as stream:
        text = stream.read()
    for master in ('sky130_fd_sc_hd__buf_2', 'sky130_fd_sc_hd__buf_8'):
        found = re.search(r'cell\s*\(\s*"?' + master + r'"?\s*\)\s*\{', text)
        if not found: raise ValueError('Missing ' + master)
        start = end = found.end(); depth = 1
        while depth and end < len(text):
            depth += (text[end] == '{') - (text[end] == '}'); end += 1
        functions = re.findall(r'(?<![A-Za-z_])function\s*:\s*"([^"]+)"\s*;', text[start:end])
        if functions not in (['A'], ['(A)']): raise ValueError('Not identity ' + master)
        checked.append(dict(lib=filename, cell=master, function=functions[0]))
Path('/audit/eco10_identity.json').write_text(json.dumps(checked, indent=2))
print('ECO10 IDENTITY LIBERTY PASS', len(checked), 'cell/library pairs')
