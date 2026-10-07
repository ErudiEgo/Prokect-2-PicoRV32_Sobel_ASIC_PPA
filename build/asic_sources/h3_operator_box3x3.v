`default_nettype none
// Exact Box3: widened additions, floor(sum/9), no border renormalization.
module h3_operator_box3x3 (
 input wire clk,rst,input wire s_valid,output wire s_ready,
 input wire [71:0] s_window,input wire [73:0] s_meta,
 output reg m_valid,input wire m_ready,output reg [7:0] m_pixel,
 output reg [73:0] m_meta
);
 wire [11:0] sum = {4'd0,s_window[7:0]}+{4'd0,s_window[15:8]}+
 {4'd0,s_window[23:16]}+{4'd0,s_window[31:24]}+{4'd0,s_window[39:32]}+
 {4'd0,s_window[47:40]}+{4'd0,s_window[55:48]}+{4'd0,s_window[63:56]}+
 {4'd0,s_window[71:64]};
/* verilator lint_off UNUSEDSIGNAL */
 wire [11:0] quotient=sum/12'd9;
/* verilator lint_on UNUSEDSIGNAL */
 assign s_ready=!rst && (!m_valid || m_ready);
 always @(posedge clk) begin
  if(rst) begin m_valid<=0;m_pixel<=0;m_meta<=0;end
  else begin
   if(m_valid && m_ready) m_valid<=0;
   if(s_valid && s_ready) begin
    m_pixel<=quotient[7:0];m_meta<=s_meta;m_valid<=1;
   end
  end
 end
endmodule
`default_nettype wire
