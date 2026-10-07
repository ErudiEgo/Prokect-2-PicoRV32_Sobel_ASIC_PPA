`default_nettype none
// Single outstanding, no combinational response. Shared reset with bus/backend.
module h3_mem_adapter_native(
 input wire clk,rst,
 input wire req_valid,output wire req_ready,input wire req_write,
 input wire [31:0] req_addr,req_wdata,input wire [3:0] req_wstrb,
 output wire rsp_valid,input wire rsp_ready,output reg [31:0] rsp_rdata,
 output wire rsp_error,
 output wire ext_valid,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata
);
 localparam IDLE=0,BUS=1,REPLY=2;
 reg [1:0] state;
 reg [31:0] address,data;
 reg [3:0] strobes;
 assign req_ready=!rst && state==IDLE;
 assign ext_valid=!rst && state==BUS;
 assign ext_addr=address;assign ext_wdata=data;assign ext_wstrb=strobes;
 assign rsp_valid=!rst && state==REPLY;
 assign rsp_error=1'b0; // Native bus has no error signal. Do not infer error coverage.
 always @(posedge clk) begin
  if(rst) begin state<=IDLE;address<=0;data<=0;strobes<=0;rsp_rdata<=0;end
  else case(state)
   IDLE: if(req_valid) begin
    address<=req_addr;data<=req_wdata;strobes<=req_write?req_wstrb:4'b0;state<=BUS;
   end
   BUS: if(ext_ready) begin rsp_rdata<=ext_rdata;state<=REPLY;end
   REPLY: if(rsp_ready) state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
`default_nettype wire
