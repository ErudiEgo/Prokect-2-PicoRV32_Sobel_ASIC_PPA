`default_nettype none
// Synthesizable CPU + Sobel peripheral with an external native memory bus.
// Program/data/image memory is outside this physical top.
module picorv32_sobel_soc #(
    parameter integer ENABLE_SOBEL = 1
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
    wire peripheral_ready;
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
            .clk(clk), .rst(!resetn), .valid(cpu_valid && peripheral_select),
            .addr(cpu_addr[7:0]), .wdata(cpu_wdata), .wstrb(cpu_wstrb),
            .ready(peripheral_ready), .rdata(peripheral_rdata)
        );
    end else begin : g_no_sobel
        // Absent device returns zero ID immediately; firmware checks presence.
        assign peripheral_ready = cpu_valid && peripheral_select;
        assign peripheral_rdata = 32'd0;
    end endgenerate
    assign ext_valid = cpu_valid && !peripheral_select && resetn;
    assign ext_instr = cpu_instr;
    assign ext_addr = cpu_addr;
    assign ext_wdata = cpu_wdata;
    assign ext_wstrb = cpu_wstrb;
    assign cpu_ready = peripheral_select ? peripheral_ready : ext_ready;
    assign cpu_rdata = peripheral_select ? peripheral_rdata : ext_rdata;
endmodule
`default_nettype wire
