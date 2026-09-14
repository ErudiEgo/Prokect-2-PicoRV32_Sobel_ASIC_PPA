# Mock-only tests: no native physical command is executed.
source $::env(SOBEL_SCRIPT_DIR)/fanout_policy.tcl
proc sobel_find_cts_master {name} {
    if {$name eq "MISSING"} {error "Missing mock master"}
    return "cell:$name"
}
proc set_max_fanout {limit objects} {lappend ::limits $limit}
proc current_design {} {return TOP}
proc sobel_original_clock_tree_synthesis {args} {
    lappend ::native_args $args
    if {[lindex $::limits end] != 6} {error "CTS target missing"}
    if {$::fail_at == [llength $::native_args]} {error "injected native failure"}
}
proc sobel_original_repair_design {args} {
    lappend ::native_args $args
    if {[lindex $::limits end] != 5} {error "Signal target missing"}
    if {$::fail_at == [llength $::native_args]} {error "injected native failure"}
}
foreach {key value} {MAX_FANOUT_CONSTRAINT 10 SOBEL_CTS_FANOUT_TARGET 6 SOBEL_SIGNAL_FANOUT_TARGET 5
    CTS_ROOT_BUFFER CLK16 CTS_DISTANCE_BETWEEN_BUFFERS 80 SOBEL_CTS_BRANCH_BUFFER_DISTANCE 1 SOBEL_POST_FANOUT_MARGIN_PCT 70} {
    set ::env($key) $value
}
set ::env(CTS_CLK_BUFFERS) {CLK4 CLK8 CLK16}
set clock_args {-root_buf CLK16 -distance_between_buffers 80}
set signal_args {-verbose -max_wire_length 0 -slew_margin 55 -cap_margin 55}
foreach command {sobel_call_cts sobel_call_repair_design} {
    set max_calls [expr {$command eq "sobel_call_cts" ? 1 : 2}]
    set args [expr {$max_calls == 1 ? $clock_args : $signal_args}]
    for {set ::fail_at 0} {$::fail_at <= $max_calls} {incr ::fail_at} {
        set ::limits {}; set ::native_args {}
        set status [catch {$command {*}$args} result]
        set expected [expr {$::fail_at ? $::fail_at : $max_calls}]
        if {[llength $::native_args] != $expected || $status != ($::fail_at != 0)} {error "Incorrect delegation/failure handling: $result"}
        if {$::limits ne [expr {$max_calls == 1 ? "6 10" : "5 10"}]} {error "Final fanout not restored"}
        if {$::fail_at && $result ne "injected native failure"} {error "Native error lost"}
        if {$max_calls == 1 && [lindex $::native_args 0] ne [concat $clock_args {-branching_point_buffers_distance 1}]} {error "CTS arguments wrong"}
        if {$max_calls == 2 && [lindex $::native_args 0] ne $signal_args} {error "First electrical pass changed"}
        if {$expected == 2 && [lindex $::native_args 1] ne {-verbose -max_wire_length 0 -slew_margin 70 -cap_margin 70}} {error "Second electrical pass wrong"}
    }
}
set ::native_args {}; set ::env(CTS_ROOT_BUFFER) MISSING
if {![catch {sobel_call_cts {*}$clock_args}] || [llength $::native_args]} {error "Missing master accepted"}
puts {FANOUT POLICY MOCK PASS: CTS options, two electrical passes, restoration on either failure; no physical command executed.}
