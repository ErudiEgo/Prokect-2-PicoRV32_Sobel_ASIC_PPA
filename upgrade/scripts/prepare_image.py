"""Prepare INPUT pixels only, never Sobel output or simulated events."""
import argparse
import hashlib
import json
from pathlib import Path


def write_input(target, width, height, pixels, provenance, channels=1, original_rgb=None):
    if not (1 <= width <= 512 and 1 <= height <= 512):
        raise ValueError("Image must be 1..512 pixels on each axis; resize explicitly first")
    if channels not in (1, 3) or (channels==3 and (width>256 or height>256)):
        raise ValueError("RGB supports 1..256 per axis with unchanged RUN16 DMA; gray supports 1..512")
    if original_rgb is not None and len(original_rgb)!=width*height*3:
        raise ValueError("Invalid original RGB preview")
    if len(pixels) != width * height * channels:
        raise ValueError("Incorrect input pixel count")
    target.mkdir(parents=True, exist_ok=False)
    hex_path = target / "image.hex"
    hex_path.write_bytes("".join(f"{p:02x}\n" for p in pixels).encode("ascii"))
    if channels==1:
        (target / "input.pgm").write_bytes(f"P5\n{width} {height}\n255\n".encode() + bytes(pixels))
    else:
        n=width*height
        interleaved=bytes(pixels[c*n+i] for i in range(n) for c in range(3))
        (target / "input.ppm").write_bytes(f"P6\n{width} {height}\n255\n".encode()+interleaved)
    if original_rgb is not None:
        (target / "original.ppm").write_bytes(f"P6\n{width} {height}\n255\n".encode()+original_rgb)
    meta = {"kind": "INPUT_ONLY", "width": width, "height": height,
            "channels": channels, "layout": "planar_RGB" if channels==3 else "gray8",
            "hex_sha256": hashlib.sha256(hex_path.read_bytes()).hexdigest(),
            "provenance": provenance}
    (target / "image.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"INPUT READY: {target.resolve()} ({width} x {height}); no CPU execution")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path, help="New directory; never overwritten")
    p.add_argument("--source", type=Path, help="PNG/JPEG/PGM etc.; Pillow required, no automatic resize")
    p.add_argument("--color", choices=("gray", "rgb"), default="gray")
    args = p.parse_args()
    original_rgb = None
    channels = 3 if args.color=="rgb" else 1
    if args.source:
        from PIL import Image
        with Image.open(args.source) as src:
            # Explicit RGB8 or RGB8 -> L conversion. No EXIF rotation or resize.
            rgb = src.convert("RGB")
            width, height = rgb.size
            original_rgb = rgb.tobytes()
            pixels = b"".join(plane.tobytes() for plane in rgb.split()) if channels==3 else rgb.convert("L").tobytes()
        provenance = {"source_name": args.source.name,
                      "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
                      "conversion": ("Pillow RGB, planar R/G/B" if channels==3 else "Pillow RGB then L") + "; no resize/EXIF rotation; alpha ignored; no ICC transform",
                      "pillow_version": Image.__version__}
    else:
        if channels==3:
            p.error("RGB needs --source; use prepare_rgb_smoke.py for deterministic inputs")
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
    write_input(args.output, width, height, pixels, provenance, channels, original_rgb)


if __name__ == "__main__":
    main()
