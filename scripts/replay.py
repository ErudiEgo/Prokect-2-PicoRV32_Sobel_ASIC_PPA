"""Desktop replay of verified RTL evidence. This never runs CPU simulation."""
import argparse
import json
import math
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk
from evidence import sha, load_image, read_hex, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="Extracted RUN folder containing comparison.json")
    args = parser.parse_args()
    directory = args.evidence.resolve()
    result = json.loads((directory / "comparison.json").read_text(encoding="utf-8"))
    if result["status"] != "PASS":
        raise ValueError("Replay requires a completed, independently checked simulation")
    for name, digest in result["evidence_sha256"].items():
        candidate = (directory / name).resolve()
        if not candidate.is_relative_to(directory) or sha(candidate) != digest:
            raise ValueError(f"Verified trace changed: {name}")
    meta, source = load_image(directory / "inputs/image")
    w, h = meta["width"], meta["height"]
    if (w,h) != (result["width"],result["height"]):
        raise ValueError("Image dimensions differ from verified output")
    frozen_hashes = json.loads((directory / "inputs.sha256.json").read_text())
    for name in ("image/image.hex", "image/image.json"):
        if sha(directory / "inputs" / name) != frozen_hashes[name]:
            raise ValueError("Frozen image changed")
    window = tk.Tk()
    window.title(f"PicoRV32 Sobel | REPLAY | {directory.name}")
    window.configure(padx=16, pady=12)
    ttk.Label(window, text="REPLAY FROM VERIFIED RTL OUTPUT", font=("Segoe UI",16,"bold")).pack()
    ttk.Label(window, text="Common elapsed CPU-cycle axis. Playback speed is not ASIC frequency or simulator wall time.").pack(pady=6)
    panels = ttk.Frame(window)
    panels.pack()
    colors = [f"#{v:02x}{v:02x}{v:02x}" for v in range(256)]
    expand = max(1, min(280//w, 280//h))
    shrink = max(1, math.ceil(max(w,h)/280))
    states = {}
    def display_image(state):
        state["display"] = state["image"].zoom(expand).subsample(shrink)
        state["label"].configure(image=state["display"])
    for n, (name, title) in enumerate((("input","Input image"),("sw","PicoRV32 software"),("hw","PicoRV32 + Sobel"))):
        frame = ttk.Frame(panels, padding=8)
        frame.grid(row=0, column=n, sticky="n")
        ttk.Label(frame, text=title, font=("Segoe UI",12,"bold")).pack()
        photo = tk.PhotoImage(width=w, height=h)
        label = ttk.Label(frame)
        label.pack(pady=8)
        info = ttk.Label(frame, text="")
        info.pack()
        state = dict(image=photo, label=label, info=info, shown=-1)
        states[name] = state
        if name == "input":
            for y in range(h):
                photo.put("{"+" ".join(colors[v] for v in source[y*w:(y+1)*w])+"}", to=(0,y))
            info.configure(text=f"{w} x {h} pixels")
        else:
            state["events"] = rows(directory / name / "tiles.csv", ["cycle","x","y","width","height","ordinal"])
            ps = rows(directory / name / "pixels.csv", ["cycle","x","y","value"])
            state["pixels"] = {p["y"]*w+p["x"]: p["value"] for p in ps}
            state["execution"] = result["modes"][name]
            photo.put("#181818", to=(0,0,w,h))
        display_image(state)
    maximum = max(result["modes"][m]["cycles"] for m in ("sw","hw"))
    position = tk.DoubleVar(value=0)
    clock_label = ttk.Label(window)
    clock_label.pack(pady=8)
    def seek(value):
        elapsed = float(value)
        clock_label.configure(text=f"Elapsed target cycles: {int(elapsed):,} / {maximum:,}")
        for name in ("sw","hw"):
            state = states[name]
            e = state["execution"]
            count = sum(t["cycle"]-e["start_cycle"] <= elapsed for t in state["events"])
            if count != state["shown"]:
                if count < state["shown"] or state["shown"] < 0:
                    state["image"].put("#181818", to=(0,0,w,h))
                    state["shown"] = 0
                for t in state["events"][state["shown"]:count]:
                    for y in range(t["y"], t["y"]+t["height"]):
                        row = " ".join(colors[state["pixels"][y*w+x]] for x in range(t["x"],t["x"]+t["width"]))
                        state["image"].put("{"+row+"}", to=(t["x"],y))
                state["shown"] = count
                display_image(state)
            done = "DONE" if elapsed >= e["cycles"] else "in progress"
            state["info"].configure(text=f"Tiles {count}/{len(state['events'])} | {done}\nMeasured total: {e['cycles']:,} cycles")
    ttk.Scale(window, from_=0, to=maximum, variable=position, command=seek, length=850).pack(fill="x")
    controls = ttk.Frame(window)
    controls.pack(pady=10)
    playing = False
    previous = time.monotonic()
    speed = tk.StringVar(value=str(max(1,round(maximum/15))))
    def toggle():
        nonlocal playing, previous
        if position.get() >= maximum:
            position.set(0)
        playing = not playing
        previous = time.monotonic()
        button.configure(text="Pause" if playing else "Play replay")
    button = ttk.Button(controls, text="Play replay", command=toggle)
    button.pack(side="left",padx=6)
    ttk.Label(controls, text="Playback cycles / screen second:").pack(side="left")
    ttk.Entry(controls, textvariable=speed, width=14).pack(side="left",padx=6)
    ttk.Label(window, text="A tile appears only after its recorded completion event. Dark areas have not been revealed yet.").pack()
    ttk.Label(window, text=f"SW/HW cycle ratio: {result['sw_cycles_div_hw_cycles']:.4f} | ASIC PPA and DRC/LVS/antenna: NOT RUN").pack(pady=5)
    def tick():
        nonlocal previous, playing
        now = time.monotonic()
        if playing:
            try:
                rate = float(speed.get())
                if not math.isfinite(rate) or rate <= 0:
                    raise ValueError()
                position.set(min(maximum, position.get()+(now-previous)*rate))
                seek(position.get())
                if position.get() >= maximum:
                    playing = False
                    button.configure(text="Play replay")
            except ValueError:
                playing = False
                button.configure(text="Play replay")
        previous = now
        window.after(40,tick)
    seek(0)
    tick()
    window.mainloop()


if __name__ == "__main__":
    main()
