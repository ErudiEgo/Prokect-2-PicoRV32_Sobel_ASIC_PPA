// Freestanding RV32I. Same source builds software-only and accelerated programs.
typedef unsigned int u32;
typedef unsigned char u8;
#define REG(a) (*(volatile u32 *)(a))
#define SOBEL_BASE 0x40000000u
#define HOST_BASE 0x40010000u
#define IMAGE ((volatile const u8 *)0x00010000u)
#define OUTPUT ((volatile u8 *)0x00050000u)
#ifndef USE_ACCEL
#define USE_ACCEL 0
#endif
static void fail(u32 code) {
    REG(HOST_BASE + 0x20u) = code;
    for (;;) { __asm__ volatile ("nop"); }
}
#if !USE_ACCEL
static u8 pixel(int x, int y, int w, int h) {
    if (x < 0 || y < 0 || x >= w || y >= h) return 0;
    // No M extension needed: GCC emits RV32I multiplication helper if necessary.
    return IMAGE[(u32)y * (u32)w + (u32)x];
}
static u8 filter(int x, int y, int w, int h) {
    int a=pixel(x-1,y-1,w,h), b=pixel(x,y-1,w,h), c=pixel(x+1,y-1,w,h);
    int d=pixel(x-1,y,w,h), e=pixel(x+1,y,w,h);
    int f=pixel(x-1,y+1,w,h), g=pixel(x,y+1,w,h), k=pixel(x+1,y+1,w,h);
    int gx=c+2*e+k-a-2*d-f;
    int gy=f+2*g+k-a-2*b-c;
    if (gx<0) gx=-gx;
    if (gy<0) gy=-gy;
    int magnitude=gx+gy;
    return (u8)(magnitude>255 ? 255 : magnitude);
}
#endif
int main(void) {
    int w=(int)REG(0xf000u), h=(int)REG(0xf004u), tile=(int)REG(0xf008u);
    if (w<1 || w>512 || h<1 || h>512 || tile<1 || tile>64) fail(1u);
#if USE_ACCEL
    if (REG(SOBEL_BASE+0x9cu)!=0x54494c31u) fail(2u);
#endif
    REG(HOST_BASE)=USE_ACCEL; // variant identity, outside measured interval
    REG(HOST_BASE+4u)=1u;     // measurement begins
#if USE_ACCEL
    REG(SOBEL_BASE+0x88u)=((u32)h<<16)|(u32)w;
#endif
    u32 tile_count=0;
    for (int ty=0; ty<h; ty+=tile) {
        for (int tx=0; tx<w; tx+=tile) {
            int ymax=ty+tile<h ? ty+tile : h;
            int xmax=tx+tile<w ? tx+tile : w;
#if USE_ACCEL
            u32 offset=(u32)ty*(u32)w+(u32)tx;
            REG(SOBEL_BASE+0x8cu)=((u32)ty<<16)|(u32)tx;
            REG(SOBEL_BASE+0x90u)=((u32)(ymax-ty)<<16)|(u32)(xmax-tx);
            REG(SOBEL_BASE+0x94u)=0x00010000u+offset;
            REG(SOBEL_BASE+0x98u)=0x00050000u+offset;
            REG(SOBEL_BASE+0x80u)=1u;
            u32 status, timeout=1000000u;
            do {
                status=REG(SOBEL_BASE+0x84u);
                if(status & 4u) fail(0x20u);
                if(--timeout==0) fail(0x21u);
            } while(!(status & 2u));
#else
            for (int y=ty; y<ymax; ++y)
                for (int x=tx; x<xmax; ++x)
                    OUTPUT[(u32)y*(u32)w+(u32)x]=filter(x,y,w,h);
#endif
            // All output stores precede the completion event on the native bus.
            REG(HOST_BASE+8u)=(u32)tx;
            REG(HOST_BASE+12u)=(u32)ty;
            REG(HOST_BASE+16u)=++tile_count;
        }
    }
    REG(HOST_BASE+4u)=2u;    // measurement ends after the final tile event
    REG(HOST_BASE+24u)=1u;   // testbench checks completion; CPU then idles
    for (;;) { __asm__ volatile ("nop"); }
    return 0;
}
