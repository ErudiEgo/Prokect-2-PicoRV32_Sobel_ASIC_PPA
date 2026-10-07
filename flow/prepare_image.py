"""Prepare INPUT pixels only, never Sobel output or simulated events."""
import argparse
import hashlib
import json
from pathlib import Path


def write_input(target, width, height, pixels, provenance):
    if not (1 <= width <= 512 and 1 <= height <= 512):
        raise ValueError("Image must be 1..512 pixels on each axis; resize explicitly first")
    if len(pixels) != width * height:
        raise ValueError("Incorrect input pixel count")
    target.mkdir(parents=True, exist_ok=False)
    hex_path = target / "image.hex"
    hex_path.write_bytes("".join(f"{p:02x}\n" for p in pixels).encode("ascii"))
    (target / "input.pgm").write_bytes(f"P5\n{width} {height}\n255\n".encode() + bytes(pixels))
    meta = {"kind": "INPUT_ONLY", "width": width, "height": height,
            "hex_sha256": hashlib.sha256(hex_path.read_bytes()).hexdigest(),
            "provenance": provenance}
    (target / "image.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"INPUT READY: {target.resolve()} ({width} x {height}); no CPU execution")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path, help="New directory; never overwritten")
    p.add_argument("--source", type=Path, help="PNG/JPEG/PGM etc.; Pillow required, no automatic resize")
    args = p.parse_args()
    if args.source:
        from PIL import Image
        with Image.open(args.source) as src:
            # Explicit RGB -> grayscale conversion. No EXIF rotation or resize.
            gray = src.convert("RGB").convert("L")
            width, height = gray.size
            pixels = gray.tobytes()
        provenance = {"source_name": args.source.name,
                      "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
                      "conversion": "Pillow RGB then L; no resize/EXIF rotation",
                      "pillow_version": Image.__version__}
    else:
        width, height = 37, 35
        # Original diagnostic stimulus: low gradients, diagonal, rectangle,
        # high-contrast crossing at x/y=32, plus partial final tiles.
        pixels = []
        for y in range(height):
            for x in range(width):
                v = (x + 2*y) % 64
                if 8 <= x <= 34 and 10 <= y <= 33:
                    v += 48
                if abs(x-y) <= 1:
                    v = 180
                if x == 32 or y == 32:
                    v = 255
                pixels.append(v)
        provenance = {"generator": "original deterministic diagnostic 37x35 v1",
                      "purpose": "whole-image borders, low gradients, clipping, tile seams and partial tiles"}
    write_input(args.output, width, height, pixels, provenance)


if __name__ == "__main__":
    main()
