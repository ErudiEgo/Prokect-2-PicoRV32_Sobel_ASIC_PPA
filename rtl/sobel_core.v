`default_nettype none
// Sobel: eight unsigned neighbours, row-major with centre omitted.
// Byte order from least significant byte: p00,p01,p02,p10,p12,p20,p21,p22.
// Accept start on an idle rising edge N; finish on edge N+1.
// start while busy is ignored. done is one cycle; result holds until next done.
module sobel_core (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [63:0] neighbors,
    output reg busy,
    output reg done,
    output reg [7:0] result
);
    wire signed [10:0] p00 = $signed({3'b000, neighbors[7:0]});
    wire signed [10:0] p01 = $signed({3'b000, neighbors[15:8]});
    wire signed [10:0] p02 = $signed({3'b000, neighbors[23:16]});
    wire signed [10:0] p10 = $signed({3'b000, neighbors[31:24]});
    wire signed [10:0] p12 = $signed({3'b000, neighbors[39:32]});
    wire signed [10:0] p20 = $signed({3'b000, neighbors[47:40]});
    wire signed [10:0] p21 = $signed({3'b000, neighbors[55:48]});
    wire signed [10:0] p22 = $signed({3'b000, neighbors[63:56]});
    reg signed [10:0] gx, gy;
    wire [10:0] abs_gx = gx[10] ? $unsigned(-gx) : $unsigned(gx);
    wire [10:0] abs_gy = gy[10] ? $unsigned(-gy) : $unsigned(gy);
    wire [11:0] magnitude = {1'b0, abs_gx} + {1'b0, abs_gy};

    always @(posedge clk) begin
        if (rst) begin
            gx <= 11'sd0;
            gy <= 11'sd0;
            busy <= 1'b0;
            done <= 1'b0;
            result <= 8'd0;
        end else begin
            done <= 1'b0;
            if (busy) begin
                result <= (magnitude > 12'd255) ? 8'd255 : magnitude[7:0];
                busy <= 1'b0;
                done <= 1'b1;
            end else if (start) begin
                gx <= p02 + (p12 <<< 1) + p22 - p00 - (p10 <<< 1) - p20;
                gy <= p20 + (p21 <<< 1) + p22 - p00 - (p01 <<< 1) - p02;
                busy <= 1'b1;
            end
        end
    end
endmodule
`default_nettype wire
