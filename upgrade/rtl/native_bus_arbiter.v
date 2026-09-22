`default_nettype none
// Non-preemptive transactions. DMA priority at idle, owner held until handshake.
// A bubble releases the previous response before choosing the next transaction.
module native_bus_arbiter (
    input wire clk, rst,
    input wire cpu_valid, cpu_instr,
    input wire [31:0] cpu_addr, cpu_wdata,
    input wire [3:0] cpu_wstrb,
    output wire cpu_ready,
    input wire dma_valid,
    input wire [31:0] dma_addr, dma_wdata,
    input wire [3:0] dma_wstrb,
    output wire dma_ready,
    output wire ext_valid, ext_instr,
    output wire [31:0] ext_addr, ext_wdata,
    output wire [3:0] ext_wstrb,
    input wire ext_ready
);
    localparam [1:0] IDLE=0, CPU=1, DMA=2;
    reg [1:0] owner;
    always @(posedge clk) begin
        if(rst) owner<=IDLE;
        else if(owner==IDLE) begin
            if(dma_valid) owner<=DMA;
            else if(cpu_valid) owner<=CPU;
        end else if(ext_valid && ext_ready) owner<=IDLE;
    end
    assign ext_valid = !rst && ((owner==DMA && dma_valid) || (owner==CPU && cpu_valid));
    assign ext_instr = owner==CPU && cpu_instr;
    assign ext_addr = owner==DMA ? dma_addr : cpu_addr;
    assign ext_wdata = owner==DMA ? dma_wdata : cpu_wdata;
    assign ext_wstrb = owner==DMA ? dma_wstrb : cpu_wstrb;
    assign cpu_ready = !rst && owner==CPU && ext_valid && ext_ready;
    assign dma_ready = !rst && owner==DMA && ext_valid && ext_ready;
endmodule
`default_nettype wire
