`default_nettype none
// Control validates descriptor/aperture before start. No in-place processing.
// done requires last successful write response; reset must include backend.
module h3_write(
 input wire clk,rst,start,
 input wire [31:0] dst_base,dst_stride,job_id,
 input wire [15:0] origin_x,origin_y,tile_w,tile_h,
 input wire s_valid,output wire s_ready,input wire [7:0] s_pixel,
 input wire [73:0] s_meta,
 output wire req_valid,input wire req_ready,output wire req_write,
 output reg [31:0] req_addr,req_wdata,output reg [3:0] req_wstrb,
 input wire rsp_valid,output wire rsp_ready,input wire rsp_error,
 output wire busy,output reg done,error,commit,
 output reg [31:0] output_count
);
 localparam IDLE=0,TOKEN=1,REQUEST=2,RESPONSE=3;
 reg [1:0] state;
 reg [31:0] row_address,pixel_address,stride,jid,total;
 reg [15:0] x,y,ox,oy,tw,th;
 wire last=(x==ox+tw-16'd1)&&(y==oy+th-16'd1);
 wire metadata_ok=s_meta[15:0]==x && s_meta[31:16]==y &&
 s_meta[39:32]==0 && s_meta[71:40]==jid &&
 s_meta[72]==(output_count==0) && s_meta[73]==last;
 assign s_ready=!rst && state==TOKEN;
 assign req_valid=!rst && state==REQUEST;assign req_write=1'b1;
 assign rsp_ready=!rst && state==RESPONSE;
 assign busy=state!=IDLE;
 always @(posedge clk) begin
  if(rst) begin
   state<=IDLE;done<=0;error<=0;commit<=0;output_count<=0;
   req_addr<=0;req_wdata<=0;req_wstrb<=0;row_address<=0;pixel_address<=0;
   stride<=0;jid<=0;total<=0;x<=0;y<=0;ox<=0;oy<=0;tw<=0;th<=0;
  end else begin
   commit<=0;
   case(state)
    IDLE:if(start) begin
     state<=TOKEN;done<=0;error<=0;output_count<=0;
     stride<=dst_stride;jid<=job_id;ox<=origin_x;oy<=origin_y;
     x<=origin_x;y<=origin_y;tw<=tile_w;th<=tile_h;
     total<={16'd0,tile_w}*{16'd0,tile_h};
     row_address<=dst_base+{16'd0,origin_y}*dst_stride+{16'd0,origin_x};
     pixel_address<=dst_base+{16'd0,origin_y}*dst_stride+{16'd0,origin_x};
    end
    TOKEN:if(s_valid) begin
     if(!metadata_ok) begin error<=1;state<=IDLE;end
     else begin
      req_addr<={pixel_address[31:2],2'b00};
      req_wstrb<=4'b1<<pixel_address[1:0];
      req_wdata<={24'd0,s_pixel} << {pixel_address[1:0],3'b0};
      state<=REQUEST;
     end
    end
    REQUEST:if(req_ready)state<=RESPONSE;
    RESPONSE:if(rsp_valid) begin
     if(rsp_error)begin error<=1;state<=IDLE;end
     else begin
      commit<=1;output_count<=output_count+32'd1;
      if(last) begin
       state<=IDLE;
       if(output_count+32'd1==total)done<=1;else error<=1;
      end else begin
       if(x==ox+tw-16'd1) begin
        x<=ox;y<=y+16'd1;row_address<=row_address+stride;pixel_address<=row_address+stride;
       end else begin x<=x+16'd1;pixel_address<=pixel_address+32'd1;end
       state<=TOKEN;
      end
     end
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
`default_nettype wire
