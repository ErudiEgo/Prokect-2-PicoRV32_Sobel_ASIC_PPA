# Project working agreement

Read README.md and OPENLANE_WORKFLOW_NOTES.md before implementation. These files record the user's established workflow; new explicit user instructions take precedence.

- Objective: a PicoRV32 SoC with a Sobel image accelerator, real CPU firmware execution, region-by-region image output, and ASIC PPA measured from actual runs.
- The user runs RTL simulation and OpenLane. Prepare sources, testbenches, firmware, constraints, scripts and commands; do not launch simulation or physical-design flows without new explicit authorization. Static checks, lint, compilation and configuration loading are allowed; distinguish them from simulation.
- Use OpenLane Classic for the requested workflow. Do not silently substitute OpenROAD Flow Scripts. The user confirmed SKY130 on 2026-09-11; use sky130A and sky130_fd_sc_hd, consistent with their prior practical work. GF180MCU is not part of the current implementation scope. Clock target and memory implementation are not finalized; verify the installed tool/PDK revisions before preparing physical runs.
- Keep the project small. Create directories when adding their actual content, not a large empty scaffold.
- Provide separate, copyable Ubuntu commands with explicit RUN names and expected success conditions. Preserve interactive terminal color/progress for user-run flows.
- Never overwrite/delete prior runs, snapshots or evidence. Freeze the inputs for each run. Link test evidence to exact RTL, firmware and relevant functional settings.
- Never fabricate image output, completion events, cycle counts or PPA. Image replay must use real simulation output and cycle timestamps. Clearly identify replay and playback speed.
- Track wall-clock simulation duration separately from target cycles and timing-derived target execution time. Compare software and accelerated execution using identical image, border handling, output arithmetic and memory conditions; include transfer and control overhead.
- Distinguish testbench-only models and host software from synthesizable ASIC hardware. Document exactly which CPU, accelerator, controllers and memories are included in the physical top.
- Do not report Sobel-only GDS/PPA as whole-SoC GDS/PPA. Do not treat FPGA resources as ASIC area or power.
- Require actual reports for PASS claims. Flow completion is not full sign-off. Report missing/unrun checks and remaining violations, including antenna and fanout. State vectorless power and IR-source/load assumptions.
- Diagnose failures from exact stage/net/corner evidence; make controlled changes. Do not disable checkers just to report success. Exam-specific exceptions from the reference conversation do not apply automatically.
- Do not rerun a flow merely to open a report, collect existing evidence or show an existing layout.
