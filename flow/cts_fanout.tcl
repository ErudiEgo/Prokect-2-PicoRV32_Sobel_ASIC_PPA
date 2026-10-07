# Delegate the complete installed OpenLane CTS script; only tighten CTS cell targets.
# OpenLane reroutes custom variables into this file, not the OS environment.
source $::env(_TCL_ENV_IN)
source $::env(SOBEL_SCRIPT_DIR)/fanout_policy.tcl
rename clock_tree_synthesis sobel_original_clock_tree_synthesis
proc clock_tree_synthesis {args} {sobel_call_cts {*}$args}
source $::env(SCRIPTS_DIR)/openroad/cts.tcl
