"""Syntax and input integrity only; never execute simulator or firmware."""
import ast
from pathlib import Path
from evidence import load_image, validate_firmware

root = Path(__file__).resolve().parents[1]
for script in sorted((root / "scripts").glob("*.py")):
    ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
manifest = validate_firmware(root)
image, _ = load_image(root / "inputs/demo")
print("PYTHON SYNTAX AND INPUT HASH CHECK PASS")
print(f"Firmware bytes: SW={manifest['images']['sw']['bytes']}, HW={manifest['images']['hw']['bytes']}")
print(f"Demo input: {image['width']} x {image['height']}")
print("No functional or physical PASS is implied.")
