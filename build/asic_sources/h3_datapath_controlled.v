`default_nettype none
// Experimental grant-fast candidate; same module name, selected ONLY by candidate runner.
// Latch owner on request acceptance; hold until registered response is consumed.
// op=0 Sobel, op=1 Box. Shared movement/window/write RTL for both.
module h3_datapath_controlled(
 input wire clk,rst,start,op,abort_job,
 output reg aborted,
 input wire [15:0] frame_w,frame_h,origin_x,origin_y,tile_w,tile_h,
 input wire [31:0] src_base,src_stride,dst_base,dst_stride,job_id,
 output reg busy,done,output wire error,
 output wire ext_valid,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata,
 output reg [31:0] output_count,output reg [63:0] cycles,reads
);
 wire launch=start&&!busy&&!rst;
 reg stopping,flush;
 wire halt=stopping || (abort_job&&busy) || error;
 wire core_rst=rst||flush;
 wire [31:0] writer_count;
 reg selected,credit;
/* verilator lint_off UNUSEDSIGNAL */
 wire rvalid,rready,rrvalid,rrready,scan_busy,scan_done,scan_error;
/* verilator lint_on UNUSEDSIGNAL */
 wire [31:0] raddr;
 wire sv,scan_ready,window_ready;wire [7:0] sample;wire [6:0] sx,sy;
 wire wv,wr;wire [71:0] win;wire [73:0] wm;
 wire sready,bready,svout,bvout;wire [7:0] sp,bp;wire [73:0] sm,bm;
/* verilator lint_off UNUSEDSIGNAL */
 wire result_ready,writer_busy,writer_done,writer_error,commit;
/* verilator lint_on UNUSEDSIGNAL */
 wire wreq,wreqready,wwrite,wrrvalid,wrrready;
 wire [31:0] wa,wd;wire [3:0] ws;
 reg [1:0] owner; // 0 none, 1 read, 2 write: held through response consumption.
 wire av,ar,rv,rr,re;wire [31:0] rd;
 assign scan_ready=window_ready&&!credit&&!halt;
 h3_scan_read_controlled reader(.clk(clk),.rst(core_rst),.start(launch),.halt(halt),.frame_w(frame_w),.frame_h(frame_h),
 .origin_x(origin_x),.origin_y(origin_y),.tile_w(tile_w),.tile_h(tile_h),
 .src_base(src_base),.src_stride(src_stride),.req_valid(rvalid),.req_ready(rready),.req_addr(raddr),
 .rsp_valid(rrvalid),.rsp_ready(rrready),.rsp_rdata(rd),.rsp_error(re),
 .s_valid(sv),.s_ready(scan_ready),.s_pixel(sample),.s_x(sx),.s_y(sy),.busy(scan_busy),.scan_done(scan_done),.error(scan_error));
 h3_window3x3 window(.clk(clk),.rst(core_rst),.start(launch),.origin_x(origin_x),.origin_y(origin_y),
 .tile_w(tile_w),.tile_h(tile_h),.job_id(job_id),.s_valid(sv&&!credit&&!halt),.s_ready(window_ready),
 .s_pixel(sample),.s_x(sx),.s_y(sy),.m_valid(wv),.m_ready(wr),.m_window(win),.m_meta(wm));
 assign wr=selected?bready:sready;
 h3_operator_sobel sobel(.clk(clk),.rst(core_rst),.s_valid(wv&&!selected),.s_ready(sready),
 .s_window(win),.s_meta(wm),.m_valid(svout),.m_ready(result_ready&&!selected&&!halt),.m_pixel(sp),.m_meta(sm));
 h3_operator_box3x3 box(.clk(clk),.rst(core_rst),.s_valid(wv&&selected),.s_ready(bready),
 .s_window(win),.s_meta(wm),.m_valid(bvout),.m_ready(result_ready&&selected&&!halt),.m_pixel(bp),.m_meta(bm));
 h3_write writer(.clk(clk),.rst(core_rst),.start(launch),.dst_base(dst_base),.dst_stride(dst_stride),
 .job_id(job_id),.origin_x(origin_x),.origin_y(origin_y),.tile_w(tile_w),.tile_h(tile_h),
 .s_valid(!halt&&(selected?bvout:svout)),.s_ready(result_ready),.s_pixel(selected?bp:sp),.s_meta(selected?bm:sm),
 .req_valid(wreq),.req_ready(wreqready),.req_write(wwrite),.req_addr(wa),.req_wdata(wd),.req_wstrb(ws),
 .rsp_valid(wrrvalid),.rsp_ready(wrrready),.rsp_error(re),.busy(writer_busy),.done(writer_done),
 .error(writer_error),.commit(commit),.output_count(writer_count));
 wire [1:0] request_owner=owner!=0?owner:(wreq?2'd2:rvalid?2'd1:2'd0);
 assign av=request_owner==1?rvalid:request_owner==2?wreq:1'b0;
 assign rready=request_owner==1&&ar;assign wreqready=request_owner==2&&ar;
 assign rrvalid=owner==1&&rv;assign wrrvalid=owner==2&&rv;
 assign rr=owner==1?rrready:owner==2?wrrready:1'b0;
 h3_mem_adapter_native adapter(.clk(clk),.rst(core_rst),.req_valid(av),.req_ready(ar),
 .req_write(request_owner==2&&wwrite),.req_addr(request_owner==2?wa:raddr),.req_wdata(wd),.req_wstrb(request_owner==2?ws:4'b0),
 .rsp_valid(rv),.rsp_ready(rr),.rsp_rdata(rd),.rsp_error(re),
 .ext_valid(ext_valid),.ext_addr(ext_addr),.ext_wdata(ext_wdata),.ext_wstrb(ext_wstrb),
 .ext_ready(ext_ready),.ext_rdata(ext_rdata));
 assign error=scan_error||writer_error;
 always @(posedge clk) begin
  if(rst)begin owner<=0;busy<=0;done<=0;selected<=0;credit<=0;cycles<=0;reads<=0;stopping<=0;flush<=0;aborted<=0;output_count<=0;end
  else begin
   flush<=0;
   if(owner==0)begin if(av&&ar)owner<=request_owner;end
   else if(rv&&rr)owner<=0;
   if(launch)begin busy<=1;done<=0;selected<=op;credit<=0;cycles<=0;reads<=0;stopping<=0;aborted<=0;output_count<=0;end
   else if(busy)begin
    cycles<=cycles+64'd1;
    output_count<=writer_count;
    if(halt)stopping<=1;
    if(rvalid&&rready)reads<=reads+64'd1;
    if(sv&&scan_ready&&sx>=2&&sy>=2)credit<=1;
    if(commit)credit<=0;
    if(!halt&&scan_done&&writer_done&&owner==0&&!ext_valid&&!rv&&!wv&&!svout&&!bvout&&!error)begin
     busy<=0;done<=1;
    end
    // All asserted client requests drain; no FETCH or new writer token after halt.
    // Internal state may reset ONLY after the adapter and both request paths idle.
    if(stopping&&owner==0&&!rvalid&&!wreq&&!rv&&ar&&!commit)begin
     output_count<=writer_count;busy<=0;done<=0;aborted<=1;flush<=1;stopping<=0;
    end
   end
  end
 end
endmodule
`default_nettype wire
