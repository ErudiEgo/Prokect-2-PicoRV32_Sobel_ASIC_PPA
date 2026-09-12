`timescale 1ns/1ps
module tb_sobel_mmio;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1, valid=0;
    reg [7:0] addr=0;
    reg [31:0] wdata=0;
    reg [3:0] wstrb=0;
    wire ready;
    wire [31:0] rdata;
    reg [31:0] value;
    integer accepted=0, issued=0;
    sobel_mmio dut(.clk(clk),.rst(rst),.valid(valid),.addr(addr),
                   .wdata(wdata),.wstrb(wstrb),.ready(ready),.rdata(rdata));
    always @(posedge clk) if (!rst && valid && ready) accepted=accepted+1;
    task automatic access(input [7:0] a, input [31:0] d, input [3:0] s, output [31:0] q);
        integer timeout;
        begin
            @(negedge clk); valid=1; addr=a; wdata=d; wstrb=s;
            issued=issued+1;
            timeout=0;
            @(posedge clk);
            while (!ready) begin
                timeout=timeout+1;
                if(timeout>10) $fatal(1,"MMIO handshake timeout");
                @(posedge clk);
            end
            q=rdata;
            @(negedge clk); valid=0;
        end
    endtask
    task automatic wr(input [7:0] a,input [31:0] d);
        reg [31:0] ignored;
        begin access(a,d,4'hf,ignored); end
    endtask
    task automatic expect_read(input [7:0] a,input [31:0] expected);
        reg [31:0] got;
        begin
            access(a,0,0,got);
            if(got!==expected) $fatal(1,"MMIO %h got=%h expected=%h",a,got,expected);
        end
    endtask
    initial begin
        repeat(3) @(negedge clk); rst=0;
        expect_read(8'h14,32'h534f424c);
        expect_read(8'h04,0);
        wr(8'h08,32'h04030201); wr(8'h0c,32'h08070605);
        expect_read(8'h08,32'h04030201); expect_read(8'h0c,32'h08070605);
        wr(8'h00,1);
        repeat(6) @(negedge clk);
        // Window [1,2,3;4,center,5;6,7,8] => Gx=6, Gy=20.
        expect_read(8'h04,2); expect_read(8'h10,26);
        expect_read(8'h04,2); // done is sticky
        wr(8'h00,4); expect_read(8'h04,0);
        access(8'h08,32'hffffffff,4'b0001,value);
        expect_read(8'h04,4); expect_read(8'h08,32'h04030201);
        wr(8'h00,2); expect_read(8'h04,0);
        expect_read(8'h09,32'hdeadbeef); expect_read(8'h04,4);
        wr(8'h00,2); wr(8'h14,0); expect_read(8'h04,4);
        wr(8'h00,2); wr(8'h08,0); wr(8'h0c,0); wr(8'h00,1);
        repeat(6) @(negedge clk);
        expect_read(8'h10,0); expect_read(8'h04,2);
        @(negedge clk); rst=1;
        repeat(2) @(negedge clk); rst=0;
        expect_read(8'h04,0); expect_read(8'h08,0); expect_read(8'h0c,0); expect_read(8'h10,0);
        if(accepted!=issued) $fatal(1,"Transaction count mismatch: %0d vs %0d",accepted,issued);
        $display("TEST PASS: sobel_mmio register, handshake, arithmetic, error and reset checks");
        $finish;
    end
    initial begin #100000; $fatal(1,"MMIO watchdog timeout"); end
endmodule
