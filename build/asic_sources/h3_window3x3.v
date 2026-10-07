`default_nettype none
// Component v1: window owns storage. Sample coordinates include halo.
// No opcode, main-memory address, or Sobel dependency.
module h3_window3x3 (
 input wire clk, rst, start,
 input wire [15:0] origin_x, origin_y, tile_w, tile_h,
 input wire [31:0] job_id,
 input wire s_valid, output wire s_ready,
 input wire [7:0] s_pixel,
 input wire [6:0] s_x, s_y,
 output reg m_valid, input wire m_ready,
 output reg [71:0] m_window,
 output reg [73:0] m_meta
);
 reg [7:0] older [0:65];
 reg [7:0] newer [0:65];
 reg [7:0] tl,tc,ml,mc,bl,bc;
 reg [15:0] ox,oy,tw,th;
 reg [31:0] jid;
 wire [7:0] top = s_y >= 2 ? older[s_x] : 8'd0;
 wire [7:0] mid = s_y >= 1 ? newer[s_x] : 8'd0;
 wire [15:0] cx = ox + {9'd0,s_x} - 16'd2;
 wire [15:0] cy = oy + {9'd0,s_y} - 16'd2;
 // Metadata LSB: x16,y16,channel8,job32,first,last.
 wire first = s_x==2 && s_y==2;
 wire last = {9'd0,s_x}==tw+16'd1 && {9'd0,s_y}==th+16'd1;
 assign s_ready = !rst && !start && (!m_valid || m_ready);
 always @(posedge clk) begin
  if (rst) begin
   m_valid<=0; m_window<=0; m_meta<=0;
   tl<=0;tc<=0;ml<=0;mc<=0;bl<=0;bc<=0;
   ox<=0;oy<=0;tw<=0;th<=0;jid<=0;
  end else if(start) begin
   m_valid<=0;tl<=0;tc<=0;ml<=0;mc<=0;bl<=0;bc<=0;
   ox<=origin_x;oy<=origin_y;tw<=tile_w;th<=tile_h;jid<=job_id;
  end else begin
   if(m_valid && m_ready) m_valid<=0;
   if(s_valid && s_ready) begin
    older[s_x]<=mid; newer[s_x]<=s_pixel;
    tl<=tc;tc<=top;ml<=mc;mc<=mid;bl<=bc;bc<=s_pixel;
    if(s_x>=2 && s_y>=2) begin
     m_window<={s_pixel,bc,bl,mid,mc,ml,top,tc,tl};
     m_meta<={last,first,jid,8'd0,cy,cx}; m_valid<=1;
    end
   end
  end
 end
endmodule
`default_nettype wire
