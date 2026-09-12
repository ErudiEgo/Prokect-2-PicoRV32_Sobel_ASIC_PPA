# Post-DRT native repair for pinned OpenROAD edf00dff. No full global_route.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
set_propagated_clock [all_clocks]
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
if {[info exists ::env(DRT_THREADS)]} { set_thread_count $::env(DRT_THREADS) } else { set_thread_count 4 }
if {![grt::have_detailed_routes]} {
    error "Native antenna repair requires existing detailed wires"
}
set diode_cell [lindex [split $::env(DIODE_CELL) "/"] 0]
# This branch is used only by the assistant's read/config preflight.
if {[info exists ::env(SOBEL_NATIVE_PREFLIGHT)] && $::env(SOBEL_NATIVE_PREFLIGHT) eq "1"} {
    help repair_antennas
    puts "NATIVE ANTENNA PREFLIGHT PASS: routed ODB loaded; layers, diode and commands prepared; no repair or routing executed"
} else {
# Native implementation uses detailed antenna geometry and incremental GRT.
# One pass per independent post-DRT check; do not clear existing dbWires.
repair_antennas $diode_cell -iterations 1 -ratio_margin $::env(GRT_ANTENNA_MARGIN)
write_views
}
