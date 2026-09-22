# Requires real LEF/Liberty and a port-only fixture or read-only loaded ODB.
# CTS delegate below is a stub: no CTS algorithm or physical edits occur.
source $::env(SOBEL_SCRIPT_DIR)/fanout_policy.tcl
set ::delegate_calls 0
# Exercise the installed Tcl parser/setters. Stop before the C++ CTS engine.
rename clock_tree_synthesis sobel_original_clock_tree_synthesis
rename cts::run_triton_cts cts::sobel_saved_engine
proc cts::run_triton_cts {} {
    incr ::delegate_calls
    return "READ_ONLY_CTS_STUB"
}
foreach name [lsort -unique [concat $::env(CTS_CLK_BUFFERS) $::env(CTS_ROOT_BUFFER)]] {
    set all [sta::find_cells_matching $name 0 0]
    if {[llength $all] < 2} {error "Regression requires duplicate timing-model names: $name"}
    puts "OLD UNIQUE-NAME GUARD WOULD FAIL: $name matches=[llength $all]"
    set cell [sobel_find_cts_master $name]
    set master [[ord::get_db] findMaster $name]
    if {[get_name [$cell library]] ne [[$master getLib] getName] ||
        [string map {_p_Cell _p_void} $cell] ne [$master staCell]} {
        error "Selected timing model instead of physical master"
    }
}
if {![catch {sobel_find_cts_master __sobel_missing_master__} message] ||
    [string first "CTS physical master not found:" $message] != 0} {
    error "Missing physical master guard failed: $message"
}
if {[sobel_call_cts -buf_list $::env(CTS_CLK_BUFFERS) -root_buf $::env(CTS_ROOT_BUFFER) -sink_clustering_enable -sink_clustering_size 8 -distance_between_buffers $::env(CTS_DISTANCE_BETWEEN_BUFFERS)] ne "READ_ONLY_CTS_STUB" || $::delegate_calls != 1} {
    error "CTS stub delegation failed"
}
puts {FANOUT CELL REGRESSION PASS: physical masters selected with multi-corner Liberty; temporary SDC applied/restored; no CTS/repair/routing/write_db.}
