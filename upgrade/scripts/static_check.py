"""Syntax and input integrity only; never execute simulator or firmware."""
import ast
from pathlib import Path
from evidence import load_image, validate_firmware
from run16_basis import validate_run16_rtl
from stage2_project import validate_project

root = Path(__file__).resolve().parents[1]
validate_project(root)
for script in sorted((root / "scripts").glob("*.py")):
    ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
validate_run16_rtl(root)
print("RUN16 RTL SOURCE MATCH (not a new physical PASS)")
manifest = validate_firmware(root)
image, _ = load_image(root / "inputs/demo")
for fixture in ("rgb_smoke32_v1", "rgb_partial17x19_v1"):
    rgb, _ = load_image(root / "inputs" / fixture)
    assert rgb["channels"]==3
print("RGB diagnostic input hashes valid")
print("PYTHON SYNTAX AND INPUT HASH CHECK PASS")
print(f"Firmware bytes: SW={manifest['images']['sw']['bytes']}, HW={manifest['images']['hw']['bytes']}")
print(f"Demo input: {image['width']} x {image['height']}")
print("No functional or physical PASS is implied.")
