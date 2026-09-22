`default_nettype none
// Synthesizable CPU + Sobel peripheral with an external native memory bus.
// Program/data/image memory is outside this physical top.
module picorv32_sobel_soc_m3 #(
    parameter integer ENABLE_SOBEL = 1,
    parameter integer DMA_VERSION = 1
) (
    input wire clk, input wire resetn,
    output wire trap,
    output wire ext_valid, output wire ext_instr,
    output wire [31:0] ext_addr, output wire [31:0] ext_wdata,
    output wire [3:0] ext_wstrb,
    input wire ext_ready, input wire [31:0] ext_rdata
);
    wire cpu_valid, cpu_instr, cpu_ready;
    wire [31:0] cpu_addr, cpu_wdata, cpu_rdata;
    wire [3:0] cpu_wstrb;
    wire peripheral_select = (cpu_addr[31:8] == 24'h400000);
    wire peripheral_ready, legacy_ready, tile_ready, external_cpu_ready;
    wire unused_tile_busy, dma_valid, dma_ready;
    wire [31:0] legacy_rdata, tile_rdata, dma_addr, dma_wdata;
    wire [3:0] dma_wstrb;
    wire [31:0] peripheral_rdata;
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
    generate if (ENABLE_SOBEL != 0) begin : g_sobel
        sobel_mmio peripheral (
            .clk(clk), .rst(!resetn), .valid(cpu_valid && peripheral_select && !cpu_addr[7]),
            .addr(cpu_addr[7:0]), .wdata(cpu_wdata), .wstrb(cpu_wstrb),
            .ready(legacy_ready), .rdata(legacy_rdata)
        );
        if (DMA_VERSION == 1) begin : g_v1
        sobel_tile tile_engine (
            .clk(clk), .rst(!resetn), .valid(cpu_valid && peripheral_select && cpu_addr[7]),
            .addr(cpu_addr[7:0]), .wdata(cpu_wdata), .wstrb(cpu_wstrb),
            .ready(tile_ready), .rdata(tile_rdata), .busy(unused_tile_busy),
            .mem_valid(dma_valid), .mem_addr(dma_addr), .mem_wdata(dma_wdata),
            .mem_wstrb(dma_wstrb), .mem_ready(dma_ready), .mem_rdata(ext_rdata)
        );
        end else begin : g_v2
        sobel_tile_v2 tile_engine (
            .clk(clk), .rst(!resetn), .valid(cpu_valid && peripheral_select && cpu_addr[7]),
            .addr(cpu_addr[7:0]), .wdata(cpu_wdata), .wstrb(cpu_wstrb),
            .ready(tile_ready), .rdata(tile_rdata), .busy(unused_tile_busy),
            .mem_valid(dma_valid), .mem_addr(dma_addr), .mem_wdata(dma_wdata),
            .mem_wstrb(dma_wstrb), .mem_ready(dma_ready), .mem_rdata(ext_rdata)
        );
        end
        assign peripheral_ready = cpu_addr[7] ? tile_ready : legacy_ready;
        assign peripheral_rdata = cpu_addr[7] ? tile_rdata : legacy_rdata;
        native_bus_arbiter arbiter (
            .clk(clk), .rst(!resetn), .cpu_valid(cpu_valid && !peripheral_select),
            .cpu_instr(cpu_instr), .cpu_addr(cpu_addr), .cpu_wdata(cpu_wdata),
            .cpu_wstrb(cpu_wstrb), .cpu_ready(external_cpu_ready),
            .dma_valid(dma_valid), .dma_addr(dma_addr), .dma_wdata(dma_wdata),
            .dma_wstrb(dma_wstrb), .dma_ready(dma_ready),
            .ext_valid(ext_valid), .ext_instr(ext_instr), .ext_addr(ext_addr),
            .ext_wdata(ext_wdata), .ext_wstrb(ext_wstrb), .ext_ready(ext_ready)
        );
    end else begin : g_no_sobel
        // Absent device returns zero ID immediately; firmware checks presence.
        assign peripheral_ready = cpu_valid && peripheral_select;
        assign peripheral_rdata = 32'd0;
        assign legacy_ready=1'b0, tile_ready=1'b0, unused_tile_busy=1'b0;
        assign legacy_rdata=32'd0, tile_rdata=32'd0;
        assign dma_valid=1'b0, dma_ready=1'b0, dma_addr=32'd0, dma_wdata=32'd0, dma_wstrb=4'd0;
        assign external_cpu_ready=ext_ready;
        assign ext_valid=cpu_valid && !peripheral_select && resetn;
        assign ext_instr=cpu_instr;
        assign ext_addr=cpu_addr;
        assign ext_wdata=cpu_wdata;
        assign ext_wstrb=cpu_wstrb;
    end endgenerate
    assign cpu_ready = peripheral_select ? peripheral_ready : external_cpu_ready;
    assign cpu_rdata = peripheral_select ? peripheral_rdata : ext_rdata;
endmodule
`default_nettype wire
