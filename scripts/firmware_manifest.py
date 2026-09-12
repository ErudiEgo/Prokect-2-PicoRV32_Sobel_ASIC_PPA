"""Publish compiled firmware with hashes; no CPU execution."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source = Path(sys.argv[1]).resolve()
    target = ROOT / "firmware/generated"
    data = {"compiler": (source / "compiler.txt").read_text(), "sources": {}, "images": {}}
    for name in ("main.c", "start.S", "link.ld"):
        if sha(source / name) != sha(ROOT / "firmware" / name):
            raise ValueError("Firmware changed during build")
        data["sources"][name] = sha(source / name)
    for mode in ("sw", "hw"):
        binary = (source / f"{mode}.bin").read_bytes()
        if not 0 < len(binary) <= 32768:
            raise ValueError("Firmware exceeds 32 KiB code budget")
        text = "".join(f"{v:02x}\n" for v in binary)
        path = target / f"{mode}.hex"
        path.write_text(text, encoding="ascii")
        data["images"][mode] = {"bytes": len(binary), "sha256": sha(path)}
    (target / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")

if __name__ == "__main__":
    main()
