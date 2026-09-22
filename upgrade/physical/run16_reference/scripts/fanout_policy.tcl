# Optimization-only fanout headroom. No physical command runs on source.
# Final/signoff SDC remains constraints.sdc (max fanout 10).
proc sobel_fanout_target {key} {
    set target $::env($key)
    set final $::env(MAX_FANOUT_CONSTRAINT)
    if {![string is integer -strict $target] || $target < 1 || $target >= $final} {
        error "Invalid optimization fanout $key=$target; must be below final limit $final"
    }
    return $target
}

# Same-name timing models may coexist with the physical ODB master.
# Select the STA Cell actually referenced by the ODB master, including when
# a library has stale same-name STA cells after read_lef/link_design.
proc sobel_find_cts_master {name} {
    set master [[ord::get_db] findMaster $name]
    if {$master eq "NULL"} {error "CTS physical master not found: $name"}
    set library [[$master getLib] getName]
    set bound [$master staCell]
    if {![regexp {^_[0-9a-fA-F]+_p_void$} $bound]} {
        error "Unsupported ODB STA binding representation for $name: $bound"
    }
    set physical {}
    set found [sta::find_cells_matching $name 0 0]
    foreach cell $found {
        # Pinned SWIG exposes master.staCell as void*, and search returns Cell*.
        # Compare identities only; never construct or dereference a cast pointer.
        if {![regexp {^_[0-9a-fA-F]+_p_Cell$} $cell]} {
            error "Unsupported STA Cell representation: $cell"
        }
        set identity [string map {_p_Cell _p_void} $cell]
        if {$identity eq $bound && [get_name $cell] eq $name &&
            [get_name [$cell library]] eq $library} {
            lappend physical $cell
        }
    }
    if {[llength $physical] != 1} {
        error "Expected one physical CTS cell $library/$name; matched [llength $physical] of [llength $found] STA cells"
    }
    puts "SOBEL CTS MASTER: $library/$name selected from [llength $found] STA matches"
    return [lindex $physical 0]
}

proc sobel_call_cts {args} {
    set target [sobel_fanout_target SOBEL_CTS_FANOUT_TARGET]
    set spacing $::env(CTS_DISTANCE_BETWEEN_BUFFERS)
    set branch $::env(SOBEL_CTS_BRANCH_BUFFER_DISTANCE)
    if {$spacing <= 0 || $branch <= 0 || $branch > $spacing} {
        error "Invalid CTS branch buffering distances: spacing=$spacing branch=$branch"
    }
    set at [lsearch -exact $args -distance_between_buffers]
    if {$at < 0 || [lindex $args [expr {$at+1}]] != $spacing ||
        [lsearch -exact $args -branching_point_buffers_distance] >= 0} {
        error "CTS spacing missing/mismatched or branch option already supplied"
    }
    lappend args -branching_point_buffers_distance $branch
    set cells {}
    foreach name [lsort -unique [concat $::env(CTS_CLK_BUFFERS) $::env(CTS_ROOT_BUFFER)]] {
        # CTS edf00dff queries the ODB master's STA Cell, not LibertyCell or top design.
        lappend cells [sobel_find_cts_master $name]
    }
    puts "SOBEL CTS: temporary master-cell fanout target=$target; final limit=$::env(MAX_FANOUT_CONSTRAINT)"
    set_max_fanout $target $cells
    try {
        ::sobel_original_clock_tree_synthesis {*}$args
    } finally {
        set_max_fanout $::env(MAX_FANOUT_CONSTRAINT) $cells
        puts "SOBEL CTS: master-cell fanout restored to final limit before timing/write_views"
    }
}

proc sobel_call_repair_design {args} {
    set target [sobel_fanout_target SOBEL_SIGNAL_FANOUT_TARGET]
    puts "SOBEL SIGNAL: temporary design fanout target=$target; reserve load budget for antenna diodes"
    set design [current_design]
    set_max_fanout $target $design
    try {
        # Revisit the newly created fanout buffers with tighter electrical headroom.
        # Native repair_design maintains incremental parasitics; the installed
        # upstream script still performs its final legalization/global routing.
        set margin $::env(SOBEL_POST_FANOUT_MARGIN_PCT)
        if {![string is integer -strict $margin] || $margin <= 0 || $margin >= 100} {
            error "Invalid post-fanout electrical margin: $margin"
        }
        set second $args
        foreach option {-slew_margin -cap_margin} {
            set at [lsearch -exact $second $option]
            if {$at < 0 || $margin < [lindex $second [expr {$at+1}]]} {
                error "Missing margin option or second pass would relax it: $option"
            }
            set second [lreplace $second [expr {$at+1}] [expr {$at+1}] $margin]
        }
        ::sobel_original_repair_design {*}$args
        puts "SOBEL SIGNAL: second electrical pass, slew/cap margins=$margin percent"
        ::sobel_original_repair_design {*}$second
    } finally {
        set_max_fanout $::env(MAX_FANOUT_CONSTRAINT) $design
        puts "SOBEL SIGNAL: fanout restored to final limit before timing/write_views"
    }
}
