`timescale 1ns/1ps
module tb_sobel_soc;
    parameter integer ENABLE_SOBEL = 1;
    localparam integer MEM_BYTES = 1048576;
    localparam integer IMAGE_BASE = 65536;
    localparam integer OUTPUT_BASE = 327680;
    reg clk=0;
    always #10 clk=~clk;
    reg resetn=0;
    wire trap, ext_valid, ext_instr;
    wire [31:0] ext_addr, ext_wdata;
    wire [3:0] ext_wstrb;
    reg ext_ready=0;
    reg [31:0] ext_rdata=0;
    picorv32_sobel_soc #(.ENABLE_SOBEL(ENABLE_SOBEL)) dut (
        .clk(clk), .resetn(resetn), .trap(trap),
        .ext_valid(ext_valid), .ext_instr(ext_instr),
        .ext_addr(ext_addr), .ext_wdata(ext_wdata), .ext_wstrb(ext_wstrb),
        .ext_ready(ext_ready), .ext_rdata(ext_rdata)
    );
    reg [7:0] memory[0:MEM_BYTES-1];
    reg written[0:262143];
    reg tile_seen[0:262143];
    integer width, height, tile_size, firmware_bytes, memory_wait, channels, ch;
    integer init_i, lane, byte_addr, index, wait_count=0;
    integer pixels_fd, tiles_fd, result_fd, tile_x=0, tile_y=0;
    integer output_count=0, tile_count=0, expected_tiles, tw, th, x, y, tile_index;
    integer identity=-1;
    reg [31:0] held_addr, held_data;
    reg [3:0] held_strobes;
    reg held_instr;
    reg measuring=0, ended=0;
    longint unsigned cycle=0, start_cycle=0, end_cycle=0;
    longint unsigned max_cycles=100000000;
    string firmware_path, image_path;
    // Observation only: never drives DUT or memory handshake. Count end-start edges.
    integer profile_fd;
    longint unsigned prof_cycles=0, cpu_idle_cycles=0, cpu_fetch_cycles=0;
    longint unsigned cpu_mmio_cycles=0, cpu_data_cycles=0, cpu_wait_cycles=0;
    longint unsigned dma_wait_cycles=0, tile_busy_cycles=0;
    longint unsigned cpu_fetch_tx=0, cpu_data_read_tx=0, cpu_data_write_tx=0;
    longint unsigned mmio_read_tx=0, mmio_write_tx=0, tile_start_tx=0, tile_status_tx=0;
    longint unsigned dma_read_tx=0, dma_write_tx=0;


    task automatic store_word(input integer address, input reg [31:0] value);
        integer n;
        begin
            for(n=0;n<4;n=n+1) memory[address+n]=value[n*8 +: 8];
        end
    endtask

    initial begin
        if (!$value$plusargs("firmware=%s",firmware_path)) $fatal(1,"Missing +firmware");
        if (!$value$plusargs("firmware_bytes=%d",firmware_bytes)) $fatal(1,"Missing firmware size");
        if (!$value$plusargs("image=%s",image_path)) $fatal(1,"Missing +image");
        if (!$value$plusargs("width=%d",width)) $fatal(1,"Missing width");
        if (!$value$plusargs("height=%d",height)) $fatal(1,"Missing height");
        if (!$value$plusargs("channels=%d",channels)) channels=1;
        if(channels!=1 && channels!=3) $fatal(1,"Invalid channel count");
        if(channels==3 && (width>256 || height>256)) $fatal(1,"RGB exceeds RUN16 DMA window");
        if (!$value$plusargs("tile=%d",tile_size)) tile_size=32;
        if (!$value$plusargs("memory_wait=%d",memory_wait)) memory_wait=1;
        if (!$value$plusargs("max_cycles=%d",max_cycles)) max_cycles=100000000;
        if(max_cycles<1 || max_cycles>2000000000) $fatal(1,"Invalid cycle watchdog");
        if(width<1 || width>512 || height<1 || height>512 || tile_size<1 || tile_size>64)
            $fatal(1,"Invalid dimensions");
        if(firmware_bytes<1 || firmware_bytes>32768 || memory_wait<0 || memory_wait>100)
            $fatal(1,"Invalid firmware/memory configuration");
        for(init_i=0;init_i<MEM_BYTES;init_i=init_i+1) memory[init_i]=0;
        for(init_i=0;init_i<width*height*channels;init_i=init_i+1) written[init_i]=0;
        expected_tiles=((width+tile_size-1)/tile_size)*((height+tile_size-1)/tile_size);
        for(init_i=0;init_i<expected_tiles;init_i=init_i+1) tile_seen[init_i]=0;
        $readmemh(firmware_path,memory,0,firmware_bytes-1);
        $readmemh(image_path,memory,IMAGE_BASE,IMAGE_BASE+width*height*channels-1);
        store_word('hf000,width); store_word('hf004,height); store_word('hf008,tile_size); store_word('hf00c,channels);
        pixels_fd=$fopen("pixels.csv","w"); tiles_fd=$fopen("tiles.csv","w");
        if(pixels_fd==0 || tiles_fd==0) $fatal(1,"Cannot create evidence files");
        if(channels==1) $fdisplay(pixels_fd,"cycle,x,y,value");
        else $fdisplay(pixels_fd,"cycle,x,y,channel,value");
        $fdisplay(tiles_fd,"cycle,x,y,width,height,ordinal");
        if($test$plusargs("vcd")) begin
            $dumpfile("soc_bus.vcd");
            // Bus evidence only; avoid dumping the 1 MiB external memory array.
            $dumpvars(0,clk,resetn,trap,ext_valid,ext_instr,ext_ready,ext_addr,ext_wdata,ext_wstrb,ext_rdata);
            $dumpvars(1,dut);
        end
        repeat(8) @(posedge clk);
        @(negedge clk); resetn=1;
    end

    // Shared external synchronous memory/host model for CPU and DMA. Writes and event timestamps occur
    // on the exact clock edge on which CPU sees valid && ready.
    always @(posedge clk) begin
        if(!resetn) begin ext_ready<=0; wait_count=0; cycle=0; end
        else begin
            cycle=cycle+1;
            if(trap) $fatal(1,"CPU trap at cycle %0d address=%h",cycle,ext_addr);
            if(cycle>max_cycles) $fatal(1,"CPU watchdog timeout at %0d cycles (limit %0d)",cycle,max_cycles);
            if(measuring) begin
                prof_cycles=prof_cycles+1;
                if(!dut.cpu_valid) cpu_idle_cycles=cpu_idle_cycles+1;
                else if(dut.peripheral_select) cpu_mmio_cycles=cpu_mmio_cycles+1;
                else if(dut.cpu_instr) cpu_fetch_cycles=cpu_fetch_cycles+1;
                else cpu_data_cycles=cpu_data_cycles+1;
                if(dut.cpu_valid && !dut.cpu_ready) cpu_wait_cycles=cpu_wait_cycles+1;
                if(dut.dma_valid && !dut.dma_ready) dma_wait_cycles=dma_wait_cycles+1;
                if(dut.unused_tile_busy) tile_busy_cycles=tile_busy_cycles+1;
                if(dut.cpu_valid && dut.cpu_ready) begin
                    if(dut.peripheral_select) begin
                        if(dut.cpu_wstrb==0) mmio_read_tx=mmio_read_tx+1;
                        else mmio_write_tx=mmio_write_tx+1;
                        if(dut.cpu_addr[7:0]==8'h80 && dut.cpu_wstrb==4'hf && dut.cpu_wdata[0]) tile_start_tx=tile_start_tx+1;
                        if(dut.cpu_addr[7:0]==8'h84 && dut.cpu_wstrb==0) tile_status_tx=tile_status_tx+1;
                    end else if(dut.cpu_instr) cpu_fetch_tx=cpu_fetch_tx+1;
                    else if(dut.cpu_wstrb==0) cpu_data_read_tx=cpu_data_read_tx+1;
                    else cpu_data_write_tx=cpu_data_write_tx+1;
                end
                if(dut.dma_valid && dut.dma_ready) begin
                    if(dut.dma_wstrb==0) dma_read_tx=dma_read_tx+1;
                    else dma_write_tx=dma_write_tx+1;
                end
            end
            ext_ready<=0;
            if(ext_valid && ext_ready) begin
                if(ext_addr!==held_addr || ext_wdata!==held_data ||
                   ext_wstrb!==held_strobes || ext_instr!==held_instr)
                    $fatal(1,"External bus changed before acceptance");
                wait_count=0;
                if(ext_wstrb!=0) begin
                    if(ext_addr<MEM_BYTES) begin
                        for(lane=0;lane<4;lane=lane+1) if(ext_wstrb[lane]) begin
                            byte_addr=(int'(ext_addr)&~3)+lane;
                            if(byte_addr>=IMAGE_BASE && byte_addr<IMAGE_BASE+width*height*channels)
                                $fatal(1,"CPU modified input image");
                            memory[byte_addr]=ext_wdata[lane*8 +: 8];
                            if(byte_addr>=OUTPUT_BASE && byte_addr<OUTPUT_BASE+width*height*channels) begin
                                if(!measuring) $fatal(1,"Output outside measured interval");
                                index=byte_addr-OUTPUT_BASE;
                                if(written[index]) $fatal(1,"Duplicate output pixel %0d",index);
                                if($isunknown(memory[byte_addr])) $fatal(1,"Unknown output pixel");
                                written[index]=1; output_count=output_count+1;
                                if(channels==1) $fdisplay(pixels_fd,"%0d,%0d,%0d,%0d",cycle,index%width,index/width,memory[byte_addr]);
                                else $fdisplay(pixels_fd,"%0d,%0d,%0d,%0d,%0d",cycle,index%width,(index%(width*height))/width,index/(width*height),memory[byte_addr]);
                            end
                        end
                    end else begin
                        if(ext_wstrb!=4'hf) $fatal(1,"Host requires full word stores");
                        case(ext_addr)
                            32'h40010000: begin
                                if(identity!=-1 || ext_wdata!=ENABLE_SOBEL) $fatal(1,"Wrong firmware identity");
                                identity=int'(ext_wdata);
                            end
                            32'h40010004: begin
                                if(ext_wdata==1 && !measuring && !ended && identity==ENABLE_SOBEL) begin
                                    measuring=1; start_cycle=cycle;
                                end else if(ext_wdata==2 && measuring) begin
                                    measuring=0; ended=1; end_cycle=cycle;
                                end else $fatal(1,"Invalid measurement marker");
                            end
                            32'h40010008: tile_x=int'(ext_wdata);
                            32'h4001000c: tile_y=int'(ext_wdata);
                            32'h40010010: begin
                                if(!measuring || tile_x<0 || tile_y<0 || tile_x>=width || tile_y>=height ||
                                   tile_x%tile_size!=0 || tile_y%tile_size!=0 || ext_wdata!=tile_count+1)
                                    $fatal(1,"Invalid tile event");
                                tile_index=(tile_y/tile_size)*((width+tile_size-1)/tile_size)+tile_x/tile_size;
                                if(tile_seen[tile_index]) $fatal(1,"Duplicate tile event");
                                tile_seen[tile_index]=1;
                                tw=(tile_x+tile_size>width)?width-tile_x:tile_size;
                                th=(tile_y+tile_size>height)?height-tile_y:tile_size;
                                for(ch=0;ch<channels;ch=ch+1)
                                for(y=tile_y;y<tile_y+th;y=y+1)
                                    for(x=tile_x;x<tile_x+tw;x=x+1)
                                        if(!written[ch*width*height+y*width+x]) $fatal(1,"Tile completed before pixel output");
                                tile_count=tile_count+1;
                                $fdisplay(tiles_fd,"%0d,%0d,%0d,%0d,%0d,%0d",cycle,tile_x,tile_y,tw,th,tile_count);
                                $display("TILE %0d/%0d mode=%0d at cycle=%0d",tile_count,expected_tiles,ENABLE_SOBEL,cycle);
                            end
                            32'h40010018: begin
                                if(ext_wdata!=1 || !ended || output_count!=width*height*channels || tile_count!=expected_tiles)
                                    $fatal(1,"Incomplete image/markers");
                                if(prof_cycles!=end_cycle-start_cycle ||
                                   prof_cycles!=cpu_idle_cycles+cpu_fetch_cycles+cpu_mmio_cycles+cpu_data_cycles)
                                    $fatal(1,"Profile cycle accounting mismatch");
                                if(ENABLE_SOBEL!=0 && (dma_write_tx!=width*height*channels || tile_start_tx!=expected_tiles*channels))
                                    $fatal(1,"Tile DMA transaction count mismatch");
                                if(ENABLE_SOBEL==0 && (dma_read_tx!=0 || dma_write_tx!=0 || tile_start_tx!=0))
                                    $fatal(1,"Software baseline unexpectedly used DMA");
                                profile_fd=$fopen("profile.json","w");
                                if(profile_fd==0)$fatal(1,"Cannot create profile");
                                $fdisplay(profile_fd,"{\"schema\":1,\"scope\":\"testbench_only\",");
                                $fdisplay(profile_fd,"\"cycles\":%0d,\"cpu_idle_cycles\":%0d,\"cpu_fetch_cycles\":%0d,",prof_cycles,cpu_idle_cycles,cpu_fetch_cycles);
                                $fdisplay(profile_fd,"\"cpu_mmio_cycles\":%0d,\"cpu_data_cycles\":%0d,\"cpu_wait_cycles\":%0d,",cpu_mmio_cycles,cpu_data_cycles,cpu_wait_cycles);
                                $fdisplay(profile_fd,"\"dma_wait_cycles\":%0d,\"tile_busy_cycles\":%0d,",dma_wait_cycles,tile_busy_cycles);
                                $fdisplay(profile_fd,"\"cpu_fetch_tx\":%0d,\"cpu_data_read_tx\":%0d,\"cpu_data_write_tx\":%0d,",cpu_fetch_tx,cpu_data_read_tx,cpu_data_write_tx);
                                $fdisplay(profile_fd,"\"mmio_read_tx\":%0d,\"mmio_write_tx\":%0d,\"tile_start_tx\":%0d,\"tile_status_tx\":%0d,",mmio_read_tx,mmio_write_tx,tile_start_tx,tile_status_tx);
                                $fdisplay(profile_fd,"\"dma_read_tx\":%0d,\"dma_write_tx\":%0d}",dma_read_tx,dma_write_tx);
                                $fclose(profile_fd);
                                result_fd=$fopen("execution.json","w");
                                if(result_fd==0) $fatal(1,"Cannot create execution.json");
                                $fdisplay(result_fd,"{\"mode\":%0d,\"width\":%0d,\"height\":%0d,\"tile\":%0d,\"memory_wait\":%0d,\"start_cycle\":%0d,\"end_cycle\":%0d,\"cycles\":%0d,\"pixels\":%0d,\"tiles\":%0d,\"channels\":%0d,\"samples\":%0d}",ENABLE_SOBEL,width,height,tile_size,memory_wait,start_cycle,end_cycle,end_cycle-start_cycle,width*height,tile_count,channels,output_count);
                                $fclose(result_fd); $fclose(pixels_fd); $fclose(tiles_fd);
                                $display("CPU EXECUTION COMPLETE: mode=%0d samples=%0d tiles=%0d cycles=%0d; golden comparison still required",ENABLE_SOBEL,output_count,tile_count,end_cycle-start_cycle);
                                $finish;
                            end
                            32'h40010020: $fatal(1,"Firmware error %h",ext_wdata);
                            default: $fatal(1,"Invalid host store %h",ext_addr);
                        endcase
                    end
                end
            end else if(ext_valid) begin
                if(wait_count==0) begin
                    held_addr=ext_addr; held_data=ext_wdata; held_strobes=ext_wstrb; held_instr=ext_instr;
                end else if(ext_addr!==held_addr || ext_wdata!==held_data || ext_wstrb!==held_strobes || ext_instr!==held_instr)
                    $fatal(1,"External request unstable during wait");
                if(wait_count>=memory_wait) begin
                    if(ext_wstrb==0) begin
                        if(ext_addr>=MEM_BYTES) $fatal(1,"Invalid memory read %h",ext_addr);
                        byte_addr=int'(ext_addr)&~3;
                        ext_rdata<={memory[byte_addr+3],memory[byte_addr+2],memory[byte_addr+1],memory[byte_addr]};
                    end else ext_rdata<=0;
                    ext_ready<=1;
                end else wait_count=wait_count+1;
            end else begin
                if(wait_count!=0) $fatal(1,"External request withdrawn");
            end
        end
    end
endmodule
