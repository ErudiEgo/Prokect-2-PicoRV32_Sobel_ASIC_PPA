`default_nettype none
// Page decode (0x40000100) belongs to future SoC wrapper. Native request offsets here.
module h3_control #(
 parameter integer SMALL_MEMORY_MAP=0,
 parameter [31:0] SRC_LO=32'h10000,SRC_HI=32'h50000,
 parameter [31:0] DST_LO=32'h50000,DST_HI=32'h90000
)(input wire clk,rst,valid,input wire [7:0] addr,
 input wire [31:0] wdata,input wire [3:0] wstrb,
 output reg ready,output reg [31:0] rdata,
 output wire ext_valid,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata);
 reg [31:0] op,shape,origin,tile,sbase,dbase,sstride,dstride,jid;
 reg busy,done,err,aborted;
 reg [31:0] code;
 reg launch,abort_pulse;
 wire ebusy,edone,eerror,eaborted;
 wire [31:0] count;
 wire [63:0] ec,reads;
 reg [63:0] cycles;
 wire [15:0] fw=shape[15:0],fh=shape[31:16];
 wire [15:0] ox=origin[15:0],oy=origin[31:16],tw=tile[15:0],th=tile[31:16];
 wire [63:0] send={32'd0,sbase}+({48'd0,fh}-64'd1)*{32'd0,sstride}+{48'd0,fw};
 wire [63:0] dend={32'd0,dbase}+({48'd0,fh}-64'd1)*{32'd0,dstride}+{48'd0,fw};
 wire [63:0] srend=(send+64'd3)&64'hfffffffffffffffc;
 wire [63:0] drend=(dend+64'd3)&64'hfffffffffffffffc;
 // Optional banked profile must agree with h3_small_memory, not the broad research aperture.
 wire banked_ok=({sbase[31:2],2'b0}>=32'h10000&&srend<=64'h10200)&&
 (({dbase[31:2],2'b0}>=32'h50000&&drend<=64'h50200)||
  ({dbase[31:2],2'b0}>=32'h60000&&drend<=64'h60200));
 wire descriptor_ok=(!SMALL_MEMORY_MAP||banked_ok)&&fw>=1&&fw<=512&&fh>=1&&fh<=512&&tw>=1&&tw<=64&&th>=1&&th<=64&&
 ({1'b0,ox}+{1'b0,tw}<={1'b0,fw})&&({1'b0,oy}+{1'b0,th}<={1'b0,fh})&&
 sstride>={16'd0,fw}&&dstride>={16'd0,fw}&&
 {sbase[31:2],2'b0}>=SRC_LO&&srend<={32'd0,SRC_HI}&&
 {dbase[31:2],2'b0}>=DST_LO&&drend<={32'd0,DST_HI}&&
 send<=64'h100000000&&dend<=64'h100000000&&
 (send<={32'd0,dbase}||dend<={32'd0,sbase});
 wire access=valid&&!ready;
 wire abort_now=access&&addr==8'h08&&wstrb==15&&wdata==2&&busy;
 h3_datapath_controlled engine(.clk(clk),.rst(rst),.start(launch),.op(op[0]),
 .abort_job(abort_pulse||abort_now),.aborted(eaborted),
 .frame_w(fw),.frame_h(fh),.origin_x(ox),.origin_y(oy),.tile_w(tw),.tile_h(th),
 .src_base(sbase),.src_stride(sstride),.dst_base(dbase),.dst_stride(dstride),.job_id(jid),
 .busy(ebusy),.done(edone),.error(eerror),.output_count(count),.cycles(ec),.reads(reads),
 .ext_valid(ext_valid),.ext_addr(ext_addr),.ext_wdata(ext_wdata),.ext_wstrb(ext_wstrb),
 .ext_ready(ext_ready),.ext_rdata(ext_rdata));
 task fault(input [31:0] value);
 begin if(!err)begin err<=1;code<=value;end end
 endtask
 always @(posedge clk)begin
  if(rst)begin
   op<=0;shape<=0;origin<=0;tile<=0;sbase<=0;dbase<=0;sstride<=0;dstride<=0;jid<=0;
   busy<=0;done<=0;err<=0;aborted<=0;code<=0;cycles<=0;launch<=0;abort_pulse<=0;ready<=0;rdata<=0;
  end else begin
   ready<=0;launch<=0;abort_pulse<=0;
   if(busy)begin
    cycles<=cycles+64'd1;
    // Ignore stale sticky completion during the launch pulse.
    if(!launch&&edone&&!abort_now&&!abort_pulse)begin busy<=0;done<=1;end
    if(!launch&&eaborted)begin busy<=0;aborted<=1;done<=0;end
   end
   if(access)begin
    ready<=1;rdata<=0;
    if(addr[1:0]!=0)fault(3);
    else if(wstrb==0)begin
     case(addr)
      8'h00:rdata<=32'h48335631;8'h04:rdata<=3;
      8'h0c:rdata<={28'd0,aborted,err,done,busy};8'h10:rdata<=code;
      8'h14:rdata<=op;8'h18:rdata<=shape;8'h1c:rdata<=origin;8'h20:rdata<=tile;
      8'h24:rdata<=sbase;8'h28:rdata<=dbase;8'h2c:rdata<=sstride;8'h30:rdata<=dstride;8'h34:rdata<=jid;
      8'h38:rdata<=cycles[31:0];8'h3c:rdata<=cycles[63:32];
      8'h40:rdata<=reads[31:0];8'h44:rdata<=reads[63:32];
      8'h48,8'h50:rdata<=count;8'h4c:rdata<=0;
      default:fault(3);
     endcase
    end else if(wstrb!=15)fault(3);
    else if(addr==8'h08)begin
     case(wdata)
      0:begin end
      1:if(busy)fault(4);
        else if(!err)begin
         if(op>1)fault(2);
         else if(!descriptor_ok)fault(1);
         else begin launch<=1;busy<=1;done<=0;aborted<=0;cycles<=0;end
        end
      2:if(busy)begin
       abort_pulse<=1;done<=0;
       if(edone&&!ebusy&&!launch)begin busy<=0;aborted<=1;end
      end
      4:if(busy)fault(3);else begin done<=0;err<=0;aborted<=0;code<=0;end
      default:fault(3);
     endcase
    end else if(busy)fault(3);
    else case(addr)
     8'h14:op<=wdata;8'h18:shape<=wdata;8'h1c:origin<=wdata;8'h20:tile<=wdata;
     8'h24:sbase<=wdata;8'h28:dbase<=wdata;8'h2c:sstride<=wdata;8'h30:dstride<=wdata;8'h34:jid<=wdata;
     default:fault(3);
    endcase
   end
   if(busy&&eerror)begin err<=1;code<=5;end
  end
 end
endmodule
`default_nettype wire
