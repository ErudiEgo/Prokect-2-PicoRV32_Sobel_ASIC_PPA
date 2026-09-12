"""USER-RUN simulation entry point. Never called by static precheck."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback

from evidence import sha, validate_firmware, load_image, golden, verify_mode

ROOT = Path(__file__).resolve().parents[1]


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def command(args, cwd, name, timeout, commands):
    print("COMMAND:", " ".join(repr(str(a)) for a in args), flush=True)
    record = {"argv": [str(a) for a in args], "cwd": str(cwd), "log": name + ".log"}
    commands.append(record)
    t0 = time.monotonic()
    with (cwd / (name + ".log")).open("w", encoding="utf-8") as log:
        process = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace", bufsize=1)
        def copy_output():
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
        reader = threading.Thread(target=copy_output)
        reader.start()
        try:
            code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            process.kill()
            process.wait()
            raise
        finally:
            reader.join()
            process.stdout.close()
            record["wall_seconds"] = time.monotonic()-t0
            record["exit_code"] = process.returncode
    if code:
        raise RuntimeError(f"{name} exited with {code}; see {cwd / (name + '.log')}")
    return record["wall_seconds"]


def execute(out):
    cfg = json.loads((out / "run_config.json").read_text())
    commands = []
    result = {"status": "INCOMPLETE", "run": out.name, "asic_checks": "NOT_RUN"}
    try:
        # This function runs from the frozen copy, including its own checker.
        hashes = json.loads((out / "inputs.sha256.json").read_text())
        for name, digest in hashes.items():
            if sha(ROOT / name) != digest:
                raise ValueError(f"Frozen input changed: {name}")
        firmware = validate_firmware(ROOT)
        meta, pixels = load_image(ROOT / "image")
        w, h = meta["width"], meta["height"]
        versions = {"python": sys.version, "platform": sys.platform}
        for tool in ("iverilog", "vvp"):
            r = subprocess.run([tool, "-V"], capture_output=True, text=True, check=True)
            versions[tool] = r.stdout + r.stderr
        save(out / "tool_versions.json", versions)
        for top, sources, success in (
            ("tb_sobel_core", ["rtl/sobel_core.v", "tb/tb_sobel_core.sv"],
             "TEST PASS: sobel_core 1283 vectors; latency, busy, done, reset checked"),
            ("tb_sobel_mmio", ["rtl/sobel_core.v", "rtl/sobel_mmio.v", "tb/tb_sobel_mmio.sv"],
             "TEST PASS: sobel_mmio register, handshake, arithmetic, error and reset checks"),
        ):
            directory = out / top
            directory.mkdir()
            command(["iverilog", "-g2012", "-Wall", "-Wno-timescale", "-s", top,
                     "-o", "sim.vvp", *[str(ROOT / s) for s in sources]], directory,
                    "compile", cfg["timeout_seconds"], commands)
            command(["vvp", "sim.vvp"], directory, "simulation", cfg["timeout_seconds"], commands)
            if success not in (directory / "simulation.log").read_text().splitlines():
                raise ValueError(f"Missing completion assertion: {top}")
        expected = golden(pixels, w, h)
        modes = {}
        sources = ["rtl/sobel_core.v", "rtl/sobel_mmio.v", "rtl/picorv32_sobel_soc.v",
                   "third_party/picorv32/picorv32.v", "tb/tb_sobel_soc.sv"]
        for index, mode in enumerate(("sw", "hw")):
            directory = out / mode
            directory.mkdir()
            command(["iverilog", "-g2012", "-Wall", "-Wno-timescale", "-s", "tb_sobel_soc",
                     f"-Ptb_sobel_soc.ENABLE_SOBEL={index}", "-o", "sim.vvp",
                     *[str(ROOT / s) for s in sources]], directory, "compile", cfg["timeout_seconds"], commands)
            elapsed = command(["vvp", "sim.vvp",
                f"+firmware={ROOT / 'firmware/generated' / (mode + '.hex')}",
                f"+firmware_bytes={firmware['images'][mode]['bytes']}",
                f"+image={ROOT / 'image/image.hex'}", f"+width={w}", f"+height={h}",
                f"+tile={cfg['tile']}", f"+memory_wait={cfg['memory_wait']}",
                *(["+vcd"] if cfg["vcd"] else [])], directory, "simulation", cfg["timeout_seconds"], commands)
            modes[mode] = verify_mode(directory, index, w, h, cfg["tile"], cfg["memory_wait"], expected)
            modes[mode]["simulation_wall_seconds"] = elapsed
            print(f"PIXEL CHECK PASS: {mode}, {w*h} pixels, all tile events verified", flush=True)
        result.update(status="PASS", width=w, height=h, modes=modes,
                      sw_cycles_div_hw_cycles=modes["sw"]["cycles"]/modes["hw"]["cycles"],
                      scope="RTL simulation only; CPU instructions execute in both variants",
                      clock_note="Cycles only. TB clock is not an ASIC timing result.")
        # Bind playback to the exact verified traces. No preview data is invented.
        result["evidence_sha256"] = {str(p.relative_to(out)).replace(os.sep,"/"): sha(p)
            for mode in ("sw", "hw") for p in (out / mode).iterdir()
            if p.name in ("pixels.csv", "tiles.csv", "execution.json", "output.pgm")}
        save(out / "comparison.json", result)
        summary = (f"FUNCTIONAL TEST PASS: {out.name}\nImage: {w} x {h}; tile={cfg['tile']}; memory_wait={cfg['memory_wait']}\n"
                   f"SW cycles: {modes['sw']['cycles']}\nHW cycles: {modes['hw']['cycles']}\n"
                   f"SW/HW cycles: {result['sw_cycles_div_hw_cycles']:.6f} (greater than 1 means faster HW)\n"
                   f"SW simulator wall seconds: {modes['sw']['simulation_wall_seconds']:.3f}\n"
                   f"HW simulator wall seconds: {modes['hw']['simulation_wall_seconds']:.3f}\n"
                   "Both outputs match independent 3x3 convolution, every pixel and tile event checked.\n"
                   "Measured interval includes pixel fetch, CPU arithmetic/control, MMIO, output stores and tile events.\n"
                   "ASIC timing, area, power, DRC, LVS, antenna and electrical checks: NOT_RUN.\n")
        (out / "SUMMARY.txt").write_text(summary, encoding="utf-8")
        print(summary, flush=True)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        result.update(status="FAIL_OR_INCOMPLETE", error=str(exc), traceback=traceback.format_exc())
        save(out / "failure.json", result)
        (out / "SUMMARY.txt").write_text(f"FAIL_OR_INCOMPLETE: {exc}\nSee logs and failure.json. ASIC checks: NOT_RUN.\n", encoding="utf-8")
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        save(out / "commands.json", commands)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--execute-frozen":
        return execute(Path(sys.argv[2]).resolve())
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run", help="Unique RUN name, e.g. soc_image_smoke_01")
    p.add_argument("--image", type=Path, default=ROOT / "inputs/demo")
    p.add_argument("--tile", type=int, default=32)
    p.add_argument("--memory-wait", type=int, default=1)
    p.add_argument("--timeout-seconds", type=int, default=600, help="Per subprocess wall-clock timeout")
    p.add_argument("--vcd", action="store_true")
    a = p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", a.run):
        p.error("Unsafe RUN name")
    if not 1 <= a.tile <= 64 or not 0 <= a.memory_wait <= 100 or a.timeout_seconds < 1:
        p.error("Invalid tile/memory wait/timeout")
    for tool in ("iverilog", "vvp"):
        if not shutil.which(tool):
            p.error(f"Missing {tool}; install Icarus Verilog in Ubuntu")
    validate_firmware(ROOT)
    load_image(a.image)
    out = ROOT / "reports" / a.run
    if out.exists() or out.with_suffix(".zip").exists():
        p.error("RUN or archive already exists. Choose a new RUN name; no overwrite allowed")
    out.mkdir(parents=True)
    frozen = out / "inputs"
    frozen.mkdir()
    for name in ("rtl", "tb", "firmware", "third_party", "scripts"):
        shutil.copytree(ROOT / name, frozen / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("README.md", "AGENTS.md", "OPENLANE_WORKFLOW_NOTES.md", "ARCHITECTURE.md"):
        shutil.copy2(ROOT / name, frozen / name)
    shutil.copytree(a.image, frozen / "image")
    cfg = {"run": a.run, "tile": a.tile, "memory_wait": a.memory_wait,
           "vcd": a.vcd, "timeout_seconds": a.timeout_seconds, "source_image": str(a.image.resolve())}
    save(out / "run_config.json", cfg)
    save(out / "inputs.sha256.json", {p.relative_to(frozen).as_posix(): sha(p) for p in sorted(frozen.rglob("*")) if p.is_file()})
    try:
        return subprocess.call([sys.executable, str(frozen / "scripts/run_soc_tests.py"), "--execute-frozen", str(out)])
    finally:
        # Archive existing evidence on failure too. This does not rerun anything.
        archive = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
        print(f"EVIDENCE: {out}\nARCHIVE: {archive}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
