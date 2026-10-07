# Refresh pin-access data AFTER ECO legalization, BEFORE producing route guides.
# This script runs only inside the user-owned physical flow.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
set_propagated_clock [all_clocks]
# GlobalRouting does not inject DRT_THREADS; DetailedRouting.run does.
# Match the reviewed launcher -j4 when no explicit value is supplied.
set h3_pin_access_threads 4
if {[info exists ::env(DRT_THREADS)]} {set h3_pin_access_threads $::env(DRT_THREADS)}
if {![string is integer -strict $h3_pin_access_threads] || $h3_pin_access_threads < 1} {
    error "Invalid DRT_THREADS for H3 pin access"
}
set_thread_count $h3_pin_access_threads
pin_access -bottom_routing_layer $::env(RT_MIN_LAYER) -top_routing_layer $::env(RT_MAX_LAYER) -verbose 1
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
puts "%OL_CREATE_REPORT antenna.rpt"
check_antennas -verbose
puts "%OL_END_REPORT"
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -global_routing
write_views
