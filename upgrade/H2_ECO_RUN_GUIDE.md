**Cập nhật 23/09: H2 ECO đã chạy và audit đạt với các giới hạn công khai. Xem [H1_H2_PPA_ACCEPTANCE.md](H1_H2_PPA_ACCEPTANCE.md). Các lệnh/tag ECO bên dưới là lịch sử, không chạy lại.**

# H2 targeted ECO — preparation 2026-09-22

Status: static preparation; physical ECO NOT_RUN. This is H2, not H3.
The earlier H2 repair01 remains FAIL: fanout 1, cap 2, slew 4. Nothing in this document supersedes its measured results.

## Controlled change

Continue from the completed pre-filler `48-sobel-antennaclosure` checkpoint of
`s2_ppa_h2_clk50_repair_01`. Parent READY hash:
`b10245c1bca95585143f187c254e02d0fdf10b4521e4599d04cde7a546cf38f7`.
Parent state SHA256: `5da1851ab04f21d33a7e28b95aeec3aad96193929dbb4ff93e66ff21ad40b87a`.
Parent ODB SHA256: `3f933ed6e30db0278ebdd74a203794c1f3dd3135a4ee9cd433204e3b03ef8696`.
Preparation refuses a different snapshot, state or ODB.

| Driver | Measured problem in repair01 | Proposed physical edit |
|---|---|---|
| `_28558_/Y`, NOR4_1, `_10606_` | SS cap/slew violation | One buf_8: NOR drives short buffer input; buffer drives original net/load |
| `_28646_/Y`, NOR4_2, `_10692_` | SS cap/slew violation | Same isolation with a second buf_8 |
| `_37271_/Q`, `origin[15]` | 13 loads: 2 logic + 11 diode_2; limit 10 | Two buf_8 branches with 7 and 6 existing input loads; FF drives two buffer inputs |

Grouping is deterministic by physical location. Every existing diode is retained;
native antenna closure may add more if needed. Buffer branches are initially placed
near load-group centroids, then legalized. Modified wires and wires attached to moved
cells are invalidated before routing. Other existing wires are retained as inputs;
the router may change routes.

Four non-inverting buffers are the only intended logic additions. The edit verifies
the original connectivity after contracting the A-to-X identity edges, preserves
original cells and ports, and checks exact connectivity again after routing. The
native antenna loop has its own guard permitting only new PDK diodes. This structural
check is not an EQY/formal-equivalence claim.

No RTL, firmware, functional data, timing limits, clock (50 ns), PDK or library change.
`SOBEL_ANTENNA_ONLY` and `SOBEL_OUTPUT_BUFFER_REPAIR` select the explicit continuation.
The old repair knobs remain inherited; no new blind margin sweep is requested.
Only the frozen derived copy of the historical output-buffer helper is replaced.
The stage1 reference and all old RUNs remain intact.

## User commands — Ubuntu

1. Copy updated sources (no simulation/PNR):

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

2. Freeze a new snapshot and run static preflight:

```bash
bash scripts/34_prepare_h2_eco.sh s2_ppa_h2_eco_clk50_01
```

Require `H2 ECO STATIC PREFLIGHT PASS` and `H2 ECO READY` before continuing.
Checks include actual ODB targets (read-only), all configured buffer Liberty truth
functions, config loading, RTL lint, port-only SDC loading, installed helper API,
six host graph tests, CLI continuation options, and PDK hashes. Mock policy tests
use fixtures; their printed fixture margins are not measurements or config overrides.
If preflight fails, stop and send its log. Do not reuse/overwrite the partial tag.

3. Run the physical continuation yourself:

```bash
bash scripts/35_run_h2_eco.sh s2_ppa_h2_eco_clk50_01
```

Classic with the existing 81-step definition is retained. `--from Sobel.AntennaClosure`
skips the inherited prefix; this is not a new full 78/81-step run. It executes buffer
insertion, legalization, routing, topology verification, antenna closure and the
remaining extraction/STA/layout/LVS/DRC/XOR checks. Native terminal color/progress is retained.
The launcher refuses a second execution under the same name and never reruns H1.

4. Collect even if the physical command ends with a deferred error:

```bash
bash scripts/36_collect_h2_eco.sh s2_ppa_h2_eco_clk50_01
```

Send the printed summary and exported `s2_ppa_h2_eco_clk50_01_collect_*.tar.gz` from
the Windows `upgrade/reports` folder. Collection performs no simulation/PNR. Inputs,
checkpoint views, source hashes, logs, reports, stage netlists and available final
views are archived. Intermediate ODBs remain in the Ubuntu RUN; preserve that folder.

## Acceptance and reporting

- Current preflight is not evidence that cap/slew/fanout or antenna have been fixed.
- Require actual post-route cap/slew/fanout and setup/hold checks at all configured
  corners, zero antenna/DRC/LVS/XOR errors, completed ECO topology check, final views,
  flow exit zero and intact provenance. Collector remains FAIL_OR_INCOMPLETE otherwise.
- Routing or new antenna diodes may reintroduce violations; four buffers do not
  guarantee closure. Diagnose exact nets/corners from this RUN before another edit.
- Runtime is continuation-only. Parent synthesis, placement, CTS and prior routing
  time are excluded. CTS evidence is inherited and explicitly recorded.
- Do not compare area/power using different evidence stages or omit this physical ECO
  from the methodology. Final H2 PPA needs independent audit before publication.
- Physical scope still excludes external program/frame RAM, pads and package.
  Vectorless power, IR-source assumptions, skipped EQY and other sign-off limitations remain.

Local successful preflight evidence is recorded under `build/h2_eco_preflight_05/`.
No physical flow or RTL simulation was launched by the assistant.

Additional host checks: `build/h2_eco_host_checks.json` verifies collector acceptance of intact continuation inputs, rejection of wrong mode/hash, and rejection of missing physical evidence. Host fixtures are under `build/h2_eco_collector_host_fixture_01`, never research RUN evidence.
