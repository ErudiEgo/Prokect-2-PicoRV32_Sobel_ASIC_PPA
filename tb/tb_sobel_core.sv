`timescale 1ns/1ps
module tb_sobel_core;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1, start = 0;
    reg [63:0] neighbors = 0;
    wire busy, done;
    wire [7:0] result;
    sobel_core dut (.clk(clk), .rst(rst), .start(start),
        .neighbors(neighbors), .busy(busy), .done(done), .result(result));
    integer checked = 0;
    integer mask, j, n;
    reg [63:0] vector;
    reg [31:0] prng = 32'h534f4245;

    // Independent integer convolution with full matrices, including centre=0.
    function automatic integer reference(input reg [63:0] pixels);
        integer p[0:8];
        integer kx[0:8];
        integer ky[0:8];
        integer i, index, sx, sy, total;
        begin
            kx[0]=-1; kx[1]=0; kx[2]=1;
            kx[3]=-2; kx[4]=0; kx[5]=2;
            kx[6]=-1; kx[7]=0; kx[8]=1;
            ky[0]=-1; ky[1]=-2; ky[2]=-1;
            ky[3]=0; ky[4]=0; ky[5]=0;
            ky[6]=1; ky[7]=2; ky[8]=1;
            index=0;
            for (i=0; i<9; i=i+1) begin
                if (i==4) p[i]=0;
                else begin p[i]=int'(pixels[index*8 +: 8]); index=index+1; end
            end
            sx=0; sy=0;
            for (i=0; i<9; i=i+1) begin sx=sx+p[i]*kx[i]; sy=sy+p[i]*ky[i]; end
            if (sx<0) sx=-sx;
            if (sy<0) sy=-sy;
            total=sx+sy;
            reference=(total>255) ? 255 : total;
        end
    endfunction

    task automatic check_vector(input reg [63:0] pixels);
        integer expected;
        reg [7:0] previous_result;
        begin
            expected=reference(pixels);
            previous_result=result;
            @(negedge clk); neighbors=pixels; start=1;
            @(posedge clk); #1;
            if (busy!==1 || done!==0 || result!==previous_result)
                $fatal(1, "FAIL: acceptance/latency/result retention");
            // Change the bus and request another operation while busy.
            @(negedge clk); neighbors=~pixels; start=1;
            @(posedge clk); #1;
            if (busy!==0 || done!==1 || result!==expected[7:0])
                $fatal(1, "FAIL: vector=%h expected=%0d got=%0d", pixels,expected,result);
            @(negedge clk); start=0;
            @(posedge clk); #1;
            if (busy!==0 || done!==0 || result!==expected[7:0])
                $fatal(1, "FAIL: done pulse/busy request/result retention");
            checked=checked+1;
        end
    endtask

    initial begin
        if ($test$plusargs("vcd")) begin $dumpfile("sobel_core.vcd"); $dumpvars(0,tb_sobel_core); end
        repeat (3) @(posedge clk);
        @(negedge clk); rst=0;
        check_vector(64'd0);
        check_vector(64'hffffffffffffffff);
        for (mask=0; mask<256; mask=mask+1) begin
            for (j=0; j<8; j=j+1) vector[j*8 +: 8]=((mask>>j)&1) ? 8'd255 : 8'd0;
            check_vector(vector);
        end
        // Small gradients exercise unsaturated outputs as well as full range.
        for (n=0; n<1024; n=n+1) begin
            for (j=0; j<8; j=j+1) begin
                prng={prng[30:0],prng[31]^prng[21]^prng[1]^prng[0]};
                vector[j*8 +: 8]=(n<512) ? {4'b0000,prng[3:0]} : prng[7:0];
            end
            check_vector(vector);
        end
        // Reset aborts an accepted operation, even when start stays asserted.
        @(negedge clk); neighbors=64'hff00000000000000; start=1;
        @(posedge clk); #1;
        if (busy!==1) $fatal(1,"FAIL: reset test did not start");
        @(negedge clk); rst=1;
        @(posedge clk); #1;
        if (busy!==0 || done!==0 || result!==0) $fatal(1,"FAIL: reset priority");
        @(negedge clk); rst=0; start=0;
        @(posedge clk); #1;
        if (busy!==0 || done!==0) $fatal(1,"FAIL: completion after abort");
        check_vector(64'h0807060504030201);
        $display("TEST PASS: sobel_core %0d vectors; latency, busy, done, reset checked",checked);
        $finish;
    end
    initial begin #1000000; $fatal(1,"FAIL: watchdog timeout"); end
endmodule
