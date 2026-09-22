# Initial laboratory assumptions, not board measurements.
# Physical clock; resetn is synchronous and timed as ordinary data.
create_clock -name clk -period $::env(CLOCK_PERIOD) [get_ports clk]
set data_inputs [get_ports {resetn ext_ready ext_rdata[*]}]
set data_outputs [all_outputs]
if {[llength $data_inputs] != 34 || [llength $data_outputs] != 71} {
    error "Expected 34 non-clock input bits and 71 output bits"
}
set_input_delay -clock clk -max 5.0 $data_inputs
set_input_delay -clock clk -min 0.5 $data_inputs
set_output_delay -clock clk -max 5.0 $data_outputs
set_output_delay -clock clk -min 0.5 $data_outputs
set_input_transition 0.1 $data_inputs
set_load [expr {$::env(OUTPUT_CAP_LOAD) / 1000.0}] $data_outputs
set_clock_uncertainty -setup 0.25 [get_clocks clk]
set_clock_uncertainty -hold 0.10 [get_clocks clk]
set_max_fanout $::env(MAX_FANOUT_CONSTRAINT) [current_design]
set_max_transition $::env(MAX_TRANSITION_CONSTRAINT) [current_design]
set_max_capacitance $::env(MAX_CAPACITANCE_CONSTRAINT) [current_design]
# No false-path or multicycle exceptions. External memory timing is assumed,
# not extracted from the testbench memory_wait setting.
