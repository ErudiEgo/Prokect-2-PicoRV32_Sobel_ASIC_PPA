"""Input validation and independent golden comparison; no simulator launch."""
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_hex(path, count):
    tokens = Path(path).read_text(encoding="ascii").split()
    if len(tokens) != count or any(len(t) != 2 or any(c not in "0123456789abcdefABCDEF" for c in t) for t in tokens):
        raise ValueError(f"Invalid byte HEX or count: {path}")
    return bytes(int(t, 16) for t in tokens)


def validate_firmware(root):
    generated = root / "firmware/generated"
    m = json.loads((generated / "manifest.json").read_text())
    if set(m["sources"]) != {"main.c", "start.S", "link.ld"}:
        raise ValueError("Incomplete firmware source manifest")
    for name, digest in m["sources"].items():
        if sha(root / "firmware" / name) != digest:
            raise ValueError(f"Stale firmware: {name} changed; rebuild firmware")
    for mode in ("sw", "hw"):
        info = m["images"][mode]
        if not 0 < info["bytes"] <= 32768 or sha(generated / f"{mode}.hex") != info["sha256"]:
            raise ValueError(f"Invalid firmware hash/size: {mode}")
        read_hex(generated / f"{mode}.hex", info["bytes"])
    return m


def load_image(path):
    m = json.loads((path / "image.json").read_text(encoding="utf-8"))
    w, h = m["width"], m["height"]
    if m["kind"] != "INPUT_ONLY" or not (1 <= w <= 512 and 1 <= h <= 512):
        raise ValueError("Invalid input metadata")
    if sha(path / "image.hex") != m["hex_sha256"]:
        raise ValueError("Input HEX hash mismatch")
    channels=m.get("channels",1)
    if channels not in (1,3) or (channels==3 and (w>256 or h>256 or m.get("layout")!="planar_RGB")):
        raise ValueError("Invalid channels/layout or RGB exceeds RUN16 DMA limits")
    return m, read_hex(path / "image.hex", w*h*channels)


def golden(pixels, width, height, channels=1):
    if channels not in (1,3) or len(pixels)!=width*height*channels:
        raise ValueError("Invalid golden input")
    if channels==3:
        n=width*height
        return b"".join(golden(pixels[c*n:(c+1)*n],width,height) for c in range(3))
    # Generic 3x3 convolution, independent of the firmware's packed 8-neighbor formula.
    kx = ((-1, 0, 1), (-2, 0, 2), (-1, 0, 1))
    ky = ((-1, -2, -1), (0, 0, 0), (1, 2, 1))
    output = []
    for y in range(height):
        for x in range(width):
            gx = gy = 0
            for j in range(3):
                for i in range(3):
                    xx, yy = x+i-1, y+j-1
                    v = pixels[yy*width+xx] if 0 <= xx < width and 0 <= yy < height else 0
                    gx += v*kx[j][i]
                    gy += v*ky[j][i]
            output.append(min(255, abs(gx)+abs(gy)))
    return bytes(output)


def rows(path, columns):
    with path.open(newline="", encoding="ascii") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != columns:
            raise ValueError(f"Wrong CSV columns: {path}")
        return [{key: int(row[key]) for key in columns} for row in reader]


def verify_mode(directory, mode, width, height, tile, memory_wait, expected, channels=1):
    e = json.loads((directory / "execution.json").read_text())
    nt = ((width+tile-1)//tile)*((height+tile-1)//tile)
    wanted = dict(mode=mode, width=width, height=height, tile=tile, memory_wait=memory_wait,
                  pixels=width*height, tiles=nt)
    if any(e.get(k) != v for k, v in wanted.items()):
        raise ValueError("Execution metadata differs from requested test")
    if e.get("channels",1)!=channels or e.get("samples",width*height)!=width*height*channels:
        raise ValueError("Channel/sample count mismatch")
    start, end = e["start_cycle"], e["end_cycle"]
    if not 0 < start < end or e["cycles"] != end-start:
        raise ValueError("Invalid measured cycle interval")
    ps = rows(directory / "pixels.csv", ["cycle", "x", "y"] + (["channel"] if channels==3 else []) + ["value"])
    ts = rows(directory / "tiles.csv", ["cycle", "x", "y", "width", "height", "ordinal"])
    if len(ps) != width*height*channels or len(ts) != nt:
        raise ValueError("Missing/extra pixels or tile events")
    values, times = {}, {}
    previous = start
    for p in ps:
        x, y, value, cycle = p["x"], p["y"], p["value"], p["cycle"]
        if not (0 <= x < width and 0 <= y < height and 0 <= value <= 255 and previous < cycle < end):
            raise ValueError("Invalid pixel value, location or timestamp")
        channel=p.get("channel",0)
        if not 0 <= channel < channels:
            raise ValueError("Invalid channel index")
        key = channel*width*height+y*width+x
        if key in values:
            raise ValueError("Duplicate pixel")
        if value != expected[key]:
            raise ValueError(f"Pixel mismatch at ({x},{y}): RTL={value}, reference={expected[key]}")
        values[key], times[key], previous = value, cycle, cycle
    previous = start
    for n, t in enumerate(ts):
        x = (n % ((width+tile-1)//tile))*tile
        y = (n // ((width+tile-1)//tile))*tile
        tw, th = min(tile, width-x), min(tile, height-y)
        if (t["x"], t["y"], t["width"], t["height"], t["ordinal"]) != (x,y,tw,th,n+1):
            raise ValueError("Invalid tile order or extent")
        if not previous < t["cycle"] < end:
            raise ValueError("Invalid tile timestamp")
        for channel in range(channels):
            for yy in range(y,y+th):
                for xx in range(x,x+tw):
                    if not previous < times[channel*width*height+yy*width+xx] < t["cycle"]:
                        raise ValueError("Channel sample written outside its tile completion interval")
        previous = t["cycle"]
    if channels==1:
        output = bytes(values[i] for i in range(width*height))
        (directory / "output.pgm").write_bytes(f"P5\n{width} {height}\n255\n".encode() + output)
    else:
        output = bytes(values[c*width*height+i] for i in range(width*height) for c in range(3))
        (directory / "output.ppm").write_bytes(f"P6\n{width} {height}\n255\n".encode() + output)
    return e
