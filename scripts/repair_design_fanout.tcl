# Delegate the installed post-GRT repair including legalization and routing.
# OpenLane reroutes custom variables into this file, not the OS environment.
source $::env(_TCL_ENV_IN)
source $::env(SOBEL_SCRIPT_DIR)/fanout_policy.tcl
rename repair_design sobel_original_repair_design
proc repair_design {args} {sobel_call_repair_design {*}$args}
source $::env(SCRIPTS_DIR)/openroad/repair_design_postgrt.tcl
