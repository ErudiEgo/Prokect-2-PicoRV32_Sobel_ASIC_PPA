module picorv32_h3_logic_ppa(input wire clk,resetn,output wire trap,
 output wire ext_valid,ext_instr,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata);endmodule
