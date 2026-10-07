`default_nettype none
// Read-only frontend component. Inputs are validated/latching control's job.
// scan_done means samples delivered, NOT job/output completion.
module h3_scan_read_controlled (
 input wire clk,rst,start,halt,
 input wire [15:0] frame_w,frame_h,origin_x,origin_y,tile_w,tile_h,
 input wire [31:0] src_base,src_stride,
 output wire req_valid,input wire req_ready,output wire [31:0] req_addr,
 input wire rsp_valid,output wire rsp_ready,input wire [31:0] rsp_rdata,
 input wire rsp_error,
 output wire s_valid,input wire s_ready,output reg [7:0] s_pixel,
 output reg [6:0] s_x,s_y,output wire busy,output reg scan_done,error
);
 localparam IDLE=0,FETCH=1,REQUEST=2,RESPONSE=3,EMIT=4,ADVANCE=5;
 reg [2:0] state;
 reg [15:0] fw,fh,ox,oy,tw,th;
/* verilator lint_off UNUSEDSIGNAL */
 reg [31:0] base,stride,address,row_pointer,pixel_pointer;
/* verilator lint_on UNUSEDSIGNAL */
 reg [1:0] lane;
 wire [16:0] gx1={1'b0,ox}+{10'd0,s_x};
 wire [16:0] gy1={1'b0,oy}+{10'd0,s_y};
 wire outside=gx1==0 || gy1==0 || gx1>{1'b0,fw} || gy1>{1'b0,fh};
 // Increment scan addresses; zero-padding suppresses reads of wrapped halo addresses.
 wire [31:0] first_pixel=src_base+{16'd0,origin_y}*src_stride+{16'd0,origin_x}-src_stride-32'd1;
 assign req_valid=!rst && state==REQUEST;
 assign req_addr=address;
 assign rsp_ready=!rst && state==RESPONSE;
 assign s_valid=!rst && state==EMIT;
 assign busy=state!=IDLE;
 always @(posedge clk) begin
  if(rst) begin
   state<=IDLE;s_pixel<=0;s_x<=0;s_y<=0;scan_done<=0;error<=0;
   fw<=0;fh<=0;ox<=0;oy<=0;tw<=0;th<=0;base<=0;stride<=0;address<=0;lane<=0;row_pointer<=0;pixel_pointer<=0;
  end else begin
   case(state)
    IDLE: if(start) begin
     fw<=frame_w;fh<=frame_h;ox<=origin_x;oy<=origin_y;tw<=tile_w;th<=tile_h;
     base<=src_base;stride<=src_stride;row_pointer<=first_pixel;pixel_pointer<=first_pixel;s_x<=0;s_y<=0;scan_done<=0;error<=0;state<=FETCH;
    end
    FETCH: if(!halt) if(outside) begin s_pixel<=0;state<=EMIT;end
      else begin address<={pixel_pointer[31:2],2'b00};lane<=pixel_pointer[1:0];state<=REQUEST;end
    REQUEST: if(req_ready) state<=RESPONSE;
    RESPONSE: if(rsp_valid) begin
     if(rsp_error) begin error<=1;state<=IDLE;end
     else begin s_pixel<=rsp_rdata[lane*8 +: 8];state<=EMIT;end
    end
    EMIT: if(s_ready) state<=ADVANCE;
    ADVANCE: if({9'd0,s_x}==tw+16'd1) begin
     if({9'd0,s_y}==th+16'd1) begin scan_done<=1;state<=IDLE;end
     else begin s_x<=0;s_y<=s_y+7'd1;row_pointer<=row_pointer+stride;pixel_pointer<=row_pointer+stride;state<=FETCH;end
    end else begin s_x<=s_x+7'd1;pixel_pointer<=pixel_pointer+32'd1;state<=FETCH;end
    default: state<=IDLE;
   endcase
  end
 end
endmodule
`default_nettype wire
