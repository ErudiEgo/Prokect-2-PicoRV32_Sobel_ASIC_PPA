# Native legality check of a prescribed assignment; no placement search or routing.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
check_placement -verbose
puts "H3 CAPACITY NATIVE PLACEMENT CHECK PASS"
write_views
report_design_area_metrics
