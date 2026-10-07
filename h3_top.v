`default_nettype none
module picorv32_h3_logic_ppa(input wire clk,resetn,output wire trap,
 output wire ext_valid,ext_instr,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata);
picorv32_h3_soc #(.SMALL_MEMORY_MAP(1)) soc(.clk(clk),.resetn(resetn),.trap(trap),.ext_valid(ext_valid),.ext_instr(ext_instr),.ext_addr(ext_addr),.ext_wdata(ext_wdata),.ext_wstrb(ext_wstrb),.ext_ready(ext_ready),.ext_rdata(ext_rdata));
endmodule
`default_nettype wire
