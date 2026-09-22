"""Parse actual OpenROAD check_antennas -verbose reports, never router estimates."""
import re


def canonical(name):
    # This project uses Verilog-escaped brackets in flattened PicoRV32 names.
    return name.replace("\\", "")


def parse_report(text):
    net = pin = layer = None
    rows = {}
    for line in text.splitlines():
        match = re.match(r"\s*(Net|Pin|Layer):\s+(\S+)", line)
        if match:
            key, value = match.groups()
            if key == "Net": net, pin, layer = value, None, None
            elif key == "Pin": pin, layer = value, None
            else: layer = value
        if "VIOLATED" in line:
            if not net or not pin or not layer or "/" not in pin:
                raise ValueError("Antenna violation lacks a complete net/pin/layer context")
            key = (canonical(net), canonical(pin))
            row = rows.setdefault(key, {"net": net, "pin": pin, "layers": []})
            if layer not in row["layers"]: row["layers"].append(layer)
    return sorted(rows.values(), key=lambda r: (r["net"], r["pin"]))


def checked_targets(text, nets, pins):
    rows = parse_report(text)
    if len(rows) != int(pins) or len({canonical(r['net']) for r in rows}) != int(nets):
        raise ValueError("Antenna report targets disagree with checker net/pin counts")
    return rows
