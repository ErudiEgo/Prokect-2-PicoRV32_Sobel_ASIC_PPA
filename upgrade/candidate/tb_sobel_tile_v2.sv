`timescale 1ns/1ps
module tb_sobel_tile_v2;
    reg clk=0; always #5 clk=~clk;
    reg rst=1,valid=0; reg [7:0] addr=0; reg [31:0] wdata=0; reg [3:0] wstrb=0;
    wire ready,busy,mv; wire [31:0] rdata,ma,mw; wire [3:0] ms;
    reg mr=0; reg [31:0] md=0;
    sobel_tile_v2 dut(.clk(clk),.rst(rst),.valid(valid),.addr(addr),.wdata(wdata),.wstrb(wstrb),
        .ready(ready),.rdata(rdata),.busy(busy),.mem_valid(mv),.mem_addr(ma),.mem_wdata(mw),
        .mem_wstrb(ms),.mem_ready(mr),.mem_rdata(md));
    reg [7:0] im[0:8191]; reg [7:0] out[0:8191]; reg seen[0:8191];
    integer i,j,n,w,h,tx,ty,tw,th,offset,waits=0,requests=0,writes=0;
    reg pending=0; reg [31:0] held_addr,held_data; reg [3:0] held_strb;
    reg [31:0] q;
    integer bias=0, pattern_id=0, reads=0, cases=0, pat, lane;
    always @(posedge clk) begin
        if(rst) begin mr<=0; pending=0; waits=0; end
        else begin
            mr<=0;
            if(mv && mr) begin
                if(!pending || ma!==held_addr || mw!==held_data || ms!==held_strb)
                    $fatal(1,"DMA changed accepted request");
                pending=0; waits=0; requests=requests+1;
                if(ms==0) reads=reads+1;
                if(ms!=0) begin
                    for(j=0;j<4;j=j+1) if(ms[j]) begin
                        offset=int'(ma)-'h50000+j-bias;
                        if(offset<0 || offset>=w*h || seen[offset]) $fatal(1,"DMA output range/duplicate");
                        seen[offset]=1; out[offset]=mw[j*8+:8]; writes=writes+1;
                    end
                end
            end else if(mv) begin
                if(!pending) begin held_addr=ma;held_data=mw;held_strb=ms;pending=1;end
                if(ma!==held_addr || mw!==held_data || ms!==held_strb) $fatal(1,"DMA unstable under backpressure");
                if(waits>=(requests%4)) begin
                    if(ms==0) begin
                        offset=int'(ma)-'h10000;
                        if(offset<0 || offset+3>=8192 || ma[1:0]!=0) $fatal(1,"DMA read range/alignment");
                        md<={im[offset+3],im[offset+2],im[offset+1],im[offset]};
                    end
                    mr<=1;
                end else waits=waits+1;
            end else if(pending) $fatal(1,"DMA withdrew request");
        end
    end
    function automatic integer pix(input integer x,y);
        if(x<0 || y<0 || x>=w || y>=h) pix=0; else pix=im[bias+y*w+x];
    endfunction
    function automatic integer reference_pixel(input integer x,y);
        integer gx,gy;
        begin
            gx=-pix(x-1,y-1)+pix(x+1,y-1)-2*pix(x-1,y)+2*pix(x+1,y)-pix(x-1,y+1)+pix(x+1,y+1);
            gy=-pix(x-1,y-1)-2*pix(x,y-1)-pix(x+1,y-1)+pix(x-1,y+1)+2*pix(x,y+1)+pix(x+1,y+1);
            if(gx<0) gx=-gx; if(gy<0) gy=-gy;
            reference_pixel=(gx+gy>255)?255:gx+gy;
        end
    endfunction
    task automatic access(input [7:0] a,input [31:0] d,input [3:0] s,output [31:0] v);
        integer limit;
        begin
            @(negedge clk); valid=1;addr=a;wdata=d;wstrb=s;limit=0;
            @(posedge clk);
            while(!ready) begin @(posedge clk);limit=limit+1;if(limit>10)$fatal(1,"Tile MMIO timeout");end
            v=rdata; @(negedge clk);valid=0;
        end
    endtask
    task automatic wr(input [7:0] a,input [31:0] d);
        reg [31:0] unused_q; begin access(a,d,4'hf,unused_q);end
    endtask
    task automatic configure;
        begin
            wr('h80,6);wr('h88,(h<<16)|w);wr('h8c,(ty<<16)|tx);
            wr('h90,(th<<16)|tw);wr('h94,'h10000+bias+ty*w+tx);wr('h98,'h50000+bias+ty*w+tx);
        end
    endtask
    task automatic run_case(input integer ww,hh,xx,yy,ttw,tth,inject_busy_write);
        integer x,y,limit,expected_count,expected_reads;
        begin
            w=ww;h=hh;tx=xx;ty=yy;tw=ttw;th=tth;writes=0;reads=0;
            for(i=0;i<8192;i=i+1) begin im[i]=(i*13+(i%5)*29)%256;seen[i]=0;out[i]=0;end
            for(i=0;i<w*h;i=i+1) begin
                case(pattern_id)
                    0: im[bias+i]=(i*13+(i%5)*29)%256;
                    1: im[bias+i]=(i%w+3*(i/w))%23;
                    2: im[bias+i]=0;
                    3: im[bias+i]=255;
                    4: im[bias+i]=(i==((h/2)*w+w/2))?255:0;
                    default: im[bias+i]=(i*i+17*i+89)%251;
                endcase
            end
            configure();wr('h80,1);
            if(inject_busy_write) begin wr('h90,0);access('h90,0,0,q);if(q!==((th<<16)|tw))$fatal(1,"Busy descriptor mutated");end
            limit=0;
            access('h84,0,0,q);
            while(q[0]) begin access('h84,0,0,q);limit=limit+1;if(limit>50000)$fatal(1,"Engine timeout");end
            if(!q[1] || q[2]!=(inject_busy_write!=0))$fatal(1,"Engine final status %h",q);
            expected_count=0;
            for(y=0;y<h;y=y+1) for(x=0;x<w;x=x+1) begin
                if(x>=tx && x<tx+tw && y>=ty && y<ty+th) begin
                    expected_count=expected_count+1;
                    if(!seen[y*w+x] || out[y*w+x]!==8'(reference_pixel(x,y)))$fatal(1,"Tile pixel mismatch %0d,%0d",x,y);
                end else if(seen[y*w+x])$fatal(1,"Write outside requested tile");
            end
            if(writes!=expected_count)$fatal(1,"Output count mismatch");
            expected_reads=0;
            for(y=ty-1;y<=ty+th;y=y+1) for(x=tx-1;x<=tx+tw;x=x+1)
                if(x>=0 && x<w && y>=0 && y<h) expected_reads=expected_reads+1;
            if(reads!=expected_reads)$fatal(1,"Read reuse mismatch actual=%0d expected=%0d",reads,expected_reads);
            cases=cases+1;
            $display("V2_CASE %0d frame=%0dx%0d origin=%0d,%0d tile=%0dx%0d lane=%0d pattern=%0d reads=%0d writes=%0d",
                cases,w,h,tx,ty,tw,th,bias,pattern_id,reads,writes);
        end
    endtask
    initial begin
        repeat(3)@(negedge clk);rst=0;
        access('h9c,0,0,q);if(q!==32'h54494c32)$fatal(1,"ABI ID");
        wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Invalid descriptor accepted");
        for(pat=0;pat<6;pat=pat+1) begin
            pattern_id=pat;
            for(lane=0;lane<4;lane=lane+1) begin
                bias=lane;
                run_case(1,1,0,0,1,1,0);
                run_case(1,7,0,2,1,3,0);
                run_case(9,1,2,0,4,1,0);
                run_case(7,5,1,1,3,2,1);
                run_case(17,19,16,16,1,3,0);
                run_case(7,5,6,4,1,1,0);
                run_case(5,5,0,1,2,3,0);
            end
            run_case(64,64,0,0,64,64,0);
            run_case(67,67,1,1,64,64,0);
        end
        // Misaligned/partial MMIO and an out-of-region source must fail closed.
        wr('h80,6);access('h88,32'hffffffff,4'b0001,q);access('h84,0,0,q);
        if(q!==4)$fatal(1,"Partial MMIO accepted");
        configure();wr('h94,0);wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Bad source accepted");
        configure();wr('h94,'h4ffff);wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Frame-end source overflow accepted");
        configure();wr('h98,'h8ffff);wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Frame-end destination overflow accepted");
        configure();wr('h94,'hffffffff);wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Address wrap accepted");
        configure();wr('h8c,(h<<16)|w);wr('h80,1);access('h84,0,0,q);if(q!==4)$fatal(1,"Outside origin accepted");
        // Reset while a memory transaction is waiting; no stale done may survive.
        configure();wr('h80,1);wait(mv);@(negedge clk);rst=1;
        repeat(2)@(negedge clk);rst=0;access('h84,0,0,q);
        if(q!==0 || mv || busy)$fatal(1,"Reset did not clear engine");
        configure();wr('h80,1);wait(mv && ms!=0);@(negedge clk);rst=1;
        repeat(2)@(negedge clk);rst=0;access('h84,0,0,q);
        if(q!==0 || mv || busy)$fatal(1,"Reset at write did not clear engine");
        bias=1;pattern_id=1;run_case(5,3,0,0,5,3,0);
        if(cases!=181)$fatal(1,"Missing test cases: %0d",cases);
        $display("TEST PASS: sobel_tile_v2 181 cases, exact pixels/read counts, borders, lanes, stalls, descriptor guards and reset");
        $finish;
    end
    initial begin #100000000;$fatal(1,"Tile unit watchdog");end
endmodule
