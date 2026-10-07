# Replay the actual RUN07 serialized environment. Physical commands are stubs.
source /design/flow/run07_global_env_fixture.tcl
# Framework supplies SCRIPTS_DIR in the process environment, not _env.tcl.
set ::env(SCRIPTS_DIR) /stub
unset -nocomplain ::env(DRT_THREADS)
if {![catch {set_thread_count $::env(DRT_THREADS)} old_error] || ![string match *DRT_THREADS* $old_error]} {error "Old failure not reproduced"}
puts "RUN07 MISSING THREAD VARIABLE REPRODUCED"
rename source real_source
proc source {path} {
 if {[string match */common/grt.tcl $path]} {
  if {[lindex $::calls end] ne "pin_access"} {error "GRT before pin access"}
  lappend ::calls global_route
 }
}
proc read_current_odb {} {lappend ::calls read}
proc all_clocks {} {return clk}
proc set_propagated_clock {args} {}
proc set_thread_count {n} {if {$n!=$::wanted_threads} {error "Wrong thread count $n"};lappend ::calls threads}
proc pin_access {args} {
 if {$args ne "-bottom_routing_layer met1 -top_routing_layer met5 -verbose 1"} {error "pin access arguments"}
 lappend ::calls pin_access
}
proc check_antennas {args} {}
proc estimate_parasitics {args} {}
proc write_views {} {lappend ::calls write}
foreach supplied {missing 2 4} {
 set calls {};set wanted_threads 4
 unset -nocomplain ::env(DRT_THREADS)
 if {$supplied ne "missing"} {set ::env(DRT_THREADS) $supplied;set wanted_threads $supplied}
 real_source /design/flow/fresh_access_grt.tcl
 if {$calls ne "read threads pin_access global_route write"} {error "Wrong order $calls"}
}
foreach bad {0 -1 invalid} {
 set calls {};set ::env(DRT_THREADS) $bad
 if {![catch {real_source /design/flow/fresh_access_grt.tcl} why] || ![string match *Invalid* $why]} {error "Invalid threads accepted"}
 if {[lsearch -exact $calls pin_access]>=0} {error "Invalid input executed pin access"}
}
puts "FRESH ACCESS ORDER MOCK PASS; missing/configured/invalid threads; actual RUN07 env; no physical steps"
exit

