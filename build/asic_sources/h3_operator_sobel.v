`default_nettype none
module h3_operator_sobel (
 input wire clk,rst,input wire s_valid,output wire s_ready,
/* verilator lint_off UNUSEDSIGNAL */
 input wire [71:0] s_window,input wire [73:0] s_meta,
/* verilator lint_on UNUSEDSIGNAL */
 output reg m_valid,input wire m_ready,output reg [7:0] m_pixel,
 output reg [73:0] m_meta
);
 reg pending;
 reg [73:0] held_meta;
 wire core_busy,core_done;
 wire [7:0] core_pixel;
 wire [63:0] neighbors={s_window[71:40],s_window[31:0]};
 assign s_ready=!rst && !pending && !m_valid && !core_busy;
 sobel_core core(.clk(clk),.rst(rst),.start(s_valid && s_ready),
 .neighbors(neighbors),.busy(core_busy),.done(core_done),.result(core_pixel));
 always @(posedge clk) begin
  if(rst) begin pending<=0;held_meta<=0;m_valid<=0;m_pixel<=0;m_meta<=0;end
  else begin
   if(m_valid && m_ready) m_valid<=0;
   if(s_valid && s_ready) begin pending<=1;held_meta<=s_meta;end
   if(core_done && pending) begin
    pending<=0;m_valid<=1;m_pixel<=core_pixel;m_meta<=held_meta;
   end
  end
 end
endmodule
`default_nettype wire
