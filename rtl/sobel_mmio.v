`default_nettype none
// Native PicoRV32 bus. Word-aligned 32-bit MMIO accesses only.
module sobel_mmio (
    input wire clk, input wire rst,
    input wire valid,
    input wire [7:0] addr,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output reg ready,
    output reg [31:0] rdata
);
    reg [63:0] neighbors;
    reg start_pulse, finished, error;
    wire busy, done;
    wire [7:0] result;
    wire active = busy | start_pulse;
    sobel_core core (.clk(clk), .rst(rst), .start(start_pulse),
        .neighbors(neighbors), .busy(busy), .done(done), .result(result));
    always @(posedge clk) begin
        if (rst) begin
            neighbors <= 64'd0;
            start_pulse <= 1'b0;
            finished <= 1'b0;
            error <= 1'b0;
            ready <= 1'b0;
            rdata <= 32'd0;
        end else begin
            ready <= 1'b0;
            start_pulse <= 1'b0;
            if (done) finished <= 1'b1;
            // ready stays high over the edge when the master accepts it;
            // do not perform the same transaction again on that edge.
            if (valid && !ready) begin
                ready <= 1'b1;
                rdata <= 32'd0;
                if (wstrb == 4'b0000) begin
                    case (addr)
                        8'h00: rdata <= 32'd0;
                        8'h04: rdata <= {29'd0, error, finished, active};
                        8'h08: rdata <= neighbors[31:0];
                        8'h0c: rdata <= neighbors[63:32];
                        8'h10: rdata <= {24'd0, result};
                        8'h14: rdata <= 32'h534f424c;
                        default: begin rdata <= 32'hdeadbeef; error <= 1'b1; end
                    endcase
                end else if (wstrb != 4'b1111) begin
                    error <= 1'b1;
                end else begin
                    case (addr)
                        8'h00: begin
                            if (wdata[1]) error <= 1'b0;
                            if (wdata[2]) finished <= 1'b0;
                            if (wdata[0]) begin
                                if (active) error <= 1'b1;
                                else begin start_pulse <= 1'b1; finished <= 1'b0; end
                            end
                        end
                        8'h08: if (active) error <= 1'b1; else neighbors[31:0] <= wdata;
                        8'h0c: if (active) error <= 1'b1; else neighbors[63:32] <= wdata;
                        default: error <= 1'b1;
                    endcase
                end
            end
        end
    end
endmodule
`default_nettype wire
