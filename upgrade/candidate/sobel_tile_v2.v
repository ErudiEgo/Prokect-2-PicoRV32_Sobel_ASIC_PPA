`default_nettype none
// Candidate TIL2: two line buffers; one byte sample per aligned bus read.
// Addresses are byte addresses; accesses on the external bus are aligned words.
module sobel_tile_v2 (
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
    localparam [3:0] IDLE=0, FETCH=1, READ=2, PUSH=3, LAUNCH=4,
        WAIT_CORE=5, WRITE=6, ADVANCE=7;
    reg [3:0] state;
    reg finished, error;
    reg [31:0] dimensions, origin, extent, source, destination;
    reg [31:0] src_row, src_pixel, dst_row, dst_pixel, read_address;
    reg [1:0] read_lane;
    reg [6:0] sx, sy;
    // Deliberately not reset. Warm-up gating prevents stale row data escaping.
    reg [7:0] older[0:65], newer[0:65];
    reg [7:0] sample_byte, top_left, top_center, mid_left, mid_center, bottom_left, bottom_center;
    reg [63:0] neighbors;
    wire core_busy, core_done;
    wire [7:0] result;
    assign busy = state != IDLE;
    sobel_core core(.clk(clk),.rst(rst),.start(state == LAUNCH),
        .neighbors(neighbors),.busy(core_busy),.done(core_done),.result(result));
    wire [7:0] top_value = sy>=2 ? older[sx] : 8'd0;
    wire [7:0] mid_value = sy>=1 ? newer[sx] : 8'd0;
    wire [16:0] scan_x_plus1 = {1'b0,origin[15:0]} + {10'd0,sx};
    wire [16:0] scan_y_plus1 = {1'b0,origin[31:16]} + {10'd0,sy};
    wire outside = scan_x_plus1==0 || scan_y_plus1==0 ||
        scan_x_plus1>{1'b0,dimensions[15:0]} || scan_y_plus1>{1'b0,dimensions[31:16]};
    wire [16:0] end_x = {1'b0,origin[15:0]}+{1'b0,extent[15:0]};
    wire [16:0] end_y = {1'b0,origin[31:16]}+{1'b0,extent[31:16]};
    wire [31:0] origin_offset = {16'd0,origin[31:16]}*{16'd0,dimensions[15:0]} + {16'd0,origin[15:0]};
    wire [31:0] frame_bytes = {16'd0,dimensions[15:0]}*{16'd0,dimensions[31:16]};
    wire [32:0] source_end = {1'b0,source} - {1'b0,origin_offset} + {1'b0,frame_bytes};
    wire [32:0] destination_end = {1'b0,destination} - {1'b0,origin_offset} + {1'b0,frame_bytes};
    wire descriptor_ok = dimensions[15:0]>=1 && dimensions[15:0]<=512 &&
        dimensions[31:16]>=1 && dimensions[31:16]<=512 &&
        extent[15:0]>=1 && extent[15:0]<=64 && extent[31:16]>=1 && extent[31:16]<=64 &&
        end_x<={1'b0,dimensions[15:0]} && end_y<={1'b0,dimensions[31:16]} &&
        {1'b0,source} >= 33'h10000+{1'b0,origin_offset} && source_end<=33'h50000 &&
        {1'b0,destination} >= 33'h50000+{1'b0,origin_offset} && destination_end<=33'h90000;
    assign mem_valid = !rst && ((state==READ) || (state==WRITE));
    assign mem_addr = state==WRITE ? {dst_pixel[31:2],2'b00} : read_address;
    assign mem_wstrb = state==WRITE ? (4'b0001 << dst_pixel[1:0]) : 4'b0000;
    assign mem_wdata = {24'd0,result} << {dst_pixel[1:0],3'b000};
    always @(posedge clk) begin
        if(rst) begin
            state<=IDLE; finished<=0; error<=0; ready<=0; rdata<=0;
            dimensions<=0; origin<=0; extent<=0; source<=0; destination<=0;
            src_row<=0; src_pixel<=0; dst_row<=0; dst_pixel<=0; read_address<=0;
            sx<=0; sy<=0; read_lane<=0; sample_byte<=0; neighbors<=0;
            top_left<=0; top_center<=0; mid_left<=0; mid_center<=0;
            bottom_left<=0; bottom_center<=0;
        end else begin
            ready<=0;
            case(state)
                FETCH: begin
                    if(outside) begin sample_byte<=0; state<=PUSH; end
                    else begin
                        read_address<={src_pixel[31:2],2'b00};
                        read_lane<=src_pixel[1:0]; state<=READ;
                    end
                end
                READ: if(mem_ready) begin
                    sample_byte<=mem_rdata[read_lane*8 +: 8]; state<=PUSH;
                end
                PUSH: begin
                    older[sx]<=mid_value; newer[sx]<=sample_byte;
                    top_left<=top_center; top_center<=top_value;
                    mid_left<=mid_center; mid_center<=mid_value;
                    bottom_left<=bottom_center; bottom_center<=sample_byte;
                    if(sx>=2 && sy>=2) begin
                        neighbors<={sample_byte,bottom_center,bottom_left,mid_value,
                                    mid_left,top_value,top_center,top_left};
                        state<=LAUNCH;
                    end else state<=ADVANCE;
                end
                LAUNCH: state<=WAIT_CORE;
                WAIT_CORE: if(core_done && !core_busy) state<=WRITE;
                WRITE: if(mem_ready) begin dst_pixel<=dst_pixel+32'd1; state<=ADVANCE; end
                ADVANCE: begin
                    if(sx==extent[15:0]+16'd1) begin
                        if(sy==extent[31:16]+16'd1) begin state<=IDLE; finished<=1; end
                        else begin
                            sx<=0; sy<=sy+7'd1; state<=FETCH;
                            src_row<=src_row+{16'd0,dimensions[15:0]};
                            src_pixel<=src_row+{16'd0,dimensions[15:0]};
                            if(sy>=2) begin
                                dst_row<=dst_row+{16'd0,dimensions[15:0]};
                                dst_pixel<=dst_row+{16'd0,dimensions[15:0]};
                            end
                        end
                    end else begin sx<=sx+7'd1; src_pixel<=src_pixel+32'd1; state<=FETCH; end
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
                        8'h9c: rdata<=32'h54494c32; // TIL2: distinct from the validated baseline
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
                                    state<=FETCH; sx<=0; sy<=0;
                                    src_row<=source-{16'd0,dimensions[15:0]}-32'd1;
                                    src_pixel<=source-{16'd0,dimensions[15:0]}-32'd1;
                                    dst_row<=destination; dst_pixel<=destination;
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
