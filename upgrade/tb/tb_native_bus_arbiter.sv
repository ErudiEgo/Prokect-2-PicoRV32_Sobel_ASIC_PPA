`timescale 1ns/1ps
module tb_native_bus_arbiter;
    reg clk=0;always #5 clk=~clk;
    reg rst=1,cv=0,dv=0;reg [31:0] ca=0,da=0;
    wire cr,dr,ev,ei;wire[31:0] ea,ew;wire[3:0] es;reg er=0;
    integer waits=0,accepted=0,cpu_count=0,dma_count=0;
    reg held=0;reg[31:0] saved;
    native_bus_arbiter dut(.clk(clk),.rst(rst),.cpu_valid(cv),.cpu_instr(1'b1),
        .cpu_addr(ca),.cpu_wdata(32'd0),.cpu_wstrb(4'd0),.cpu_ready(cr),
        .dma_valid(dv),.dma_addr(da),.dma_wdata(32'h12345678),.dma_wstrb(4'hf),.dma_ready(dr),
        .ext_valid(ev),.ext_instr(ei),.ext_addr(ea),.ext_wdata(ew),.ext_wstrb(es),.ext_ready(er));
    always @(posedge clk) begin
        if(rst)begin er<=0;held=0;waits=0;end
        else begin
            er<=0;
            if(cr && dr)$fatal(1,"Both masters acknowledged");
            if(ev && er)begin
                if(!held || ea!==saved)$fatal(1,"Owner changed before acceptance");
                if(cr)begin
                    if(!cv || ea!==ca || es!==0 || !ei || ew!==0)$fatal(1,"CPU response misrouted");
                    cpu_count=cpu_count+1;
                end else if(dr)begin
                    if(!dv || ea!==da || es!==4'hf || ei || ew!==32'h12345678)$fatal(1,"DMA response misrouted");
                    dma_count=dma_count+1;
                end else $fatal(1,"Lost response");
                accepted=accepted+1;held=0;waits=0;
            end else if(ev)begin
                if(!held)begin saved=ea;held=1;end
                if(ea!==saved)$fatal(1,"Request changed during stall");
                if(waits>=accepted%5)er<=1;else waits=waits+1;
            end else if(held)$fatal(1,"Request withdrawn");
        end
    end
    initial begin
        repeat(3)@(negedge clk);rst=0;
        fork
            begin
                for(integer c=0;c<12;c=c+1)begin
                    @(negedge clk);cv=1;ca=32'h1000+4*c;
                    @(posedge clk);while(!cr)@(posedge clk);
                    @(negedge clk);cv=0;
                end
            end
            begin
                for(integer d=0;d<20;d=d+1)begin
                    @(negedge clk);dv=1;da=32'h2000+4*d;
                    @(posedge clk);while(!dr)@(posedge clk);
                    @(negedge clk);dv=0;
                end
            end
        join
        repeat(3)@(negedge clk);
        if(cpu_count!=12 || dma_count!=20 || ev)$fatal(1,"Arbiter transaction counts");
        // Abort an outstanding transaction on global reset.
        cv=1;ca=32'h3000;wait(ev);@(negedge clk);rst=1;cv=0;
        repeat(2)@(negedge clk);rst=0;repeat(2)@(negedge clk);
        if(ev || cr || dr)$fatal(1,"Arbiter reset left transaction active");
        $display("TEST PASS: native_bus_arbiter contention, backpressure, ownership and reset");
        $finish;
    end
    initial begin #1000000;$fatal(1,"Arbiter unit watchdog");end
endmodule
