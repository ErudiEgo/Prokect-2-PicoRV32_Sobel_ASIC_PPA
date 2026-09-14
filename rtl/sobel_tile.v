`default_nettype none
// Finite per-tile DMA engine. Memory is external; this RTL owns all computation.
// Addresses are byte addresses; accesses on the external bus are aligned words.
module sobel_tile (
    input wire clk, rst, valid,
    input wire [7:0] addr,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output reg ready,
    output reg [31:0] rdata,
    output wire busy,
    output wire mem_valid,
    output wire [31:0] mem_addr, mem_wdata,
    output wire [3:0] mem_wstrb,
    input wire mem_ready,
    input wire [31:0] mem_rdata
);
    localparam [2:0] IDLE=0, FETCH=1, READ=2, LAUNCH=3, WAIT_CORE=4, WRITE=5;
    reg [2:0] state;
    reg finished, error;
    reg [31:0] dimensions, origin, extent, source, destination;
    reg [31:0] src_row, dst_row, src_pixel, dst_pixel, read_address;
    reg [1:0] read_lane;
    reg [15:0] px, py, ix, iy;
    reg [2:0] neighbor_index;
    reg [63:0] neighbors;
    wire core_busy, core_done;
    wire [7:0] result;
    assign busy = state != IDLE;
    sobel_core core(.clk(clk),.rst(rst),.start(state == LAUNCH),
        .neighbors(neighbors),.busy(core_busy),.done(core_done),.result(result));
    wire left_col = neighbor_index==0 || neighbor_index==3 || neighbor_index==5;
    wire right_col = neighbor_index==2 || neighbor_index==4 || neighbor_index==7;
    wire upper_row = neighbor_index<3;
    wire lower_row = neighbor_index>4;
    wire outside = (left_col && px==0) || (right_col && px==dimensions[15:0]-16'd1)
                 || (upper_row && py==0) || (lower_row && py==dimensions[31:16]-16'd1);
    wire [31:0] neighbor_row = upper_row ? src_pixel-{16'd0,dimensions[15:0]} :
                              lower_row ? src_pixel+{16'd0,dimensions[15:0]} : src_pixel;
    wire [31:0] neighbor_address = left_col ? neighbor_row-32'd1 :
                                  right_col ? neighbor_row+32'd1 : neighbor_row;
    wire [16:0] end_x = {1'b0,origin[15:0]}+{1'b0,extent[15:0]};
    wire [16:0] end_y = {1'b0,origin[31:16]}+{1'b0,extent[31:16]};
    wire descriptor_ok = dimensions[15:0]>=1 && dimensions[15:0]<=512 &&
        dimensions[31:16]>=1 && dimensions[31:16]<=512 &&
        extent[15:0]>=1 && extent[15:0]<=64 && extent[31:16]>=1 && extent[31:16]<=64 &&
        end_x<={1'b0,dimensions[15:0]} && end_y<={1'b0,dimensions[31:16]} &&
        source>=32'h00010000 && source<32'h00050000 &&
        destination>=32'h00050000 && destination<32'h00090000;
    assign mem_valid = (state==READ) || (state==WRITE);
    assign mem_addr = state==WRITE ? {dst_pixel[31:2],2'b00} : read_address;
    assign mem_wstrb = state==WRITE ? (4'b0001 << dst_pixel[1:0]) : 4'b0000;
    assign mem_wdata = {24'd0,result} << {dst_pixel[1:0],3'b000};
    always @(posedge clk) begin
        if(rst) begin
            state<=IDLE; finished<=0; error<=0; ready<=0; rdata<=0;
            dimensions<=0; origin<=0; extent<=0; source<=0; destination<=0;
            src_row<=0; dst_row<=0; src_pixel<=0; dst_pixel<=0; read_address<=0;
            read_lane<=0; px<=0; py<=0; ix<=0; iy<=0; neighbor_index<=0; neighbors<=0;
        end else begin
            ready<=0;
            case(state)
                FETCH: begin
                    if(outside) begin
                        neighbors[neighbor_index*8 +: 8]<=0;
                        if(neighbor_index==7) state<=LAUNCH;
                        else neighbor_index<=neighbor_index+3'd1;
                    end else if(neighbor_address<32'h00010000 || neighbor_address>=32'h00050000) begin
                        error<=1; finished<=0; state<=IDLE;
                    end else begin
                        read_address<={neighbor_address[31:2],2'b00};
                        read_lane<=neighbor_address[1:0]; state<=READ;
                    end
                end
                READ: if(mem_ready) begin
                    neighbors[neighbor_index*8 +: 8]<=mem_rdata[read_lane*8 +: 8];
                    if(neighbor_index==7) state<=LAUNCH;
                    else begin neighbor_index<=neighbor_index+3'd1; state<=FETCH; end
                end
                LAUNCH: state<=WAIT_CORE;
                WAIT_CORE: if(core_done && !core_busy) begin
                    if(dst_pixel<32'h00050000 || dst_pixel>=32'h00090000) begin
                        error<=1; finished<=0; state<=IDLE;
                    end else state<=WRITE;
                end
                WRITE: if(mem_ready) begin
                    if(ix==extent[15:0]-16'd1 && iy==extent[31:16]-16'd1) begin
                        state<=IDLE; finished<=1;
                    end else begin
                        neighbor_index<=0; state<=FETCH;
                        if(ix==extent[15:0]-16'd1) begin
                            ix<=0; iy<=iy+16'd1; px<=origin[15:0]; py<=py+16'd1;
                            src_row<=src_row+{16'd0,dimensions[15:0]};
                            dst_row<=dst_row+{16'd0,dimensions[15:0]};
                            src_pixel<=src_row+{16'd0,dimensions[15:0]};
                            dst_pixel<=dst_row+{16'd0,dimensions[15:0]};
                        end else begin
                            ix<=ix+16'd1; px<=px+16'd1;
                            src_pixel<=src_pixel+32'd1; dst_pixel<=dst_pixel+32'd1;
                        end
                    end
                end
                default: begin end
            endcase
            // One transaction per valid/ready acceptance, matching legacy MMIO.
            if(valid && !ready) begin
                ready<=1; rdata<=0;
                if(wstrb==0) begin
                    case(addr)
                        8'h80: rdata<=0;
                        8'h84: rdata<={29'd0,error,finished,busy};
                        8'h88: rdata<=dimensions;
                        8'h8c: rdata<=origin;
                        8'h90: rdata<=extent;
                        8'h94: rdata<=source;
                        8'h98: rdata<=destination;
                        8'h9c: rdata<=32'h54494c31; // TIL1 ABI
                        default: begin error<=1; rdata<=32'hdeadbeef; end
                    endcase
                end else if(wstrb!=4'hf) error<=1;
                else if(busy) error<=1; // no descriptor/start mutation mid-tile
                else begin
                    case(addr)
                        8'h80: begin
                            if(wdata[1]) error<=0;
                            if(wdata[2]) finished<=0;
                            if(wdata[0]) begin
                                finished<=0;
                                if(!descriptor_ok || (error && !wdata[1])) error<=1;
                                else begin
                                    state<=FETCH; ix<=0; iy<=0; neighbor_index<=0;
                                    px<=origin[15:0]; py<=origin[31:16];
                                    src_row<=source; dst_row<=destination;
                                    src_pixel<=source; dst_pixel<=destination;
                                end
                            end
                        end
                        8'h88: dimensions<=wdata;
                        8'h8c: origin<=wdata;
                        8'h90: extent<=wdata;
                        8'h94: source<=wdata;
                        8'h98: destination<=wdata;
                        default: error<=1;
                    endcase
                end
            end
        end
    end
endmodule
`default_nettype wire
