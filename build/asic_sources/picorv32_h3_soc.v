`default_nettype none
// CPU + retained legacy Sobel + H3. External memory excluded; H2 not instantiated.
module picorv32_h3_soc #(parameter integer SMALL_MEMORY_MAP=0)(input wire clk,resetn,output wire trap,
 output wire ext_valid,ext_instr,output wire [31:0] ext_addr,ext_wdata,
 output wire [3:0] ext_wstrb,input wire ext_ready,input wire [31:0] ext_rdata);
 wire cpu_valid,cpu_instr,cpu_ready;wire [31:0] cpu_addr,cpu_wdata,cpu_rdata;wire [3:0] cpu_wstrb;
 wire hs=cpu_addr[31:8]==24'h400001;
 wire ls=cpu_addr[31:8]==24'h400000;
 wire hr,lr,cr,dr,dv;wire [31:0] hd,ld,da,dw;wire [3:0] ds;
    // Explicitly named unused optional interfaces; original CPU kept unmodified.
    wire unused_la_read, unused_la_write, unused_pcpi_valid, unused_trace_valid;
    wire [31:0] unused_la_addr, unused_la_wdata, unused_pcpi_insn;
    wire [31:0] unused_pcpi_rs1, unused_pcpi_rs2, unused_eoi;
    wire [3:0] unused_la_wstrb;
    wire [35:0] unused_trace_data;
    picorv32 #(
        .ENABLE_COUNTERS(1), .ENABLE_COUNTERS64(1),
        .ENABLE_REGS_16_31(1), .ENABLE_REGS_DUALPORT(1),
        .BARREL_SHIFTER(1), .COMPRESSED_ISA(0),
        .ENABLE_MUL(0), .ENABLE_DIV(0), .ENABLE_IRQ(0), .ENABLE_PCPI(0),
        .PROGADDR_RESET(32'h00000000), .STACKADDR(32'h0000f000)
    ) cpu (
        .clk(clk), .resetn(resetn), .trap(trap),
        .mem_valid(cpu_valid), .mem_instr(cpu_instr), .mem_ready(cpu_ready),
        .mem_addr(cpu_addr), .mem_wdata(cpu_wdata), .mem_wstrb(cpu_wstrb), .mem_rdata(cpu_rdata),
        .mem_la_read(unused_la_read), .mem_la_write(unused_la_write),
        .mem_la_addr(unused_la_addr), .mem_la_wdata(unused_la_wdata), .mem_la_wstrb(unused_la_wstrb),
        .pcpi_valid(unused_pcpi_valid), .pcpi_insn(unused_pcpi_insn),
        .pcpi_rs1(unused_pcpi_rs1), .pcpi_rs2(unused_pcpi_rs2),
        .pcpi_wr(1'b0), .pcpi_rd(32'd0), .pcpi_wait(1'b0), .pcpi_ready(1'b0),
        .irq(32'd0), .eoi(unused_eoi),
        .trace_valid(unused_trace_valid), .trace_data(unused_trace_data)
    );
 h3_control #(.SMALL_MEMORY_MAP(SMALL_MEMORY_MAP)) h3(.clk(clk),.rst(!resetn),.valid(cpu_valid&&hs),.addr(cpu_addr[7:0]),
 .wdata(cpu_wdata),.wstrb(cpu_wstrb),.ready(hr),.rdata(hd),
 .ext_valid(dv),.ext_addr(da),.ext_wdata(dw),.ext_wstrb(ds),.ext_ready(dr),.ext_rdata(ext_rdata));
 sobel_mmio legacy(.clk(clk),.rst(!resetn),.valid(cpu_valid&&ls),.addr(cpu_addr[7:0]),
 .wdata(cpu_wdata),.wstrb(cpu_wstrb),.ready(lr),.rdata(ld));
 native_bus_arbiter arbiter(.clk(clk),.rst(!resetn),.cpu_valid(cpu_valid&&!hs&&!ls),
 .cpu_instr(cpu_instr),.cpu_addr(cpu_addr),.cpu_wdata(cpu_wdata),.cpu_wstrb(cpu_wstrb),.cpu_ready(cr),
 .dma_valid(dv),.dma_addr(da),.dma_wdata(dw),.dma_wstrb(ds),.dma_ready(dr),
 .ext_valid(ext_valid),.ext_instr(ext_instr),.ext_addr(ext_addr),.ext_wdata(ext_wdata),.ext_wstrb(ext_wstrb),.ext_ready(ext_ready));
 assign cpu_ready=hs?hr:ls?lr:cr;
 assign cpu_rdata=hs?hd:ls?ld:ext_rdata;
endmodule
`default_nettype wire
