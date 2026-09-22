/* S1 firmware: same image/tile/channel/output contract as preserved S0/H1. */
#include "sobel_s1.h"
typedef unsigned int u32;
typedef unsigned char u8;
#define REG(a) (*(volatile u32 *)(a))
#define HOST_BASE 0x40010000u
#define IMAGE_BASE 0x00010000u
#define OUTPUT_BASE 0x00050000u
static void fail(u32 code) {
    REG(HOST_BASE + 0x20u) = code;
    for (;;) { __asm__ volatile ("nop"); }
}
int main(void) {
    int w=(int)REG(0xf000u), h=(int)REG(0xf004u), tile=(int)REG(0xf008u);
    u32 channels=REG(0xf00cu);
    if (channels!=1u && channels!=3u) fail(3u);
    if (channels==3u && (w>256 || h>256)) fail(4u);
    if (w<1 || w>512 || h<1 || h>512 || tile<1 || tile>64) fail(1u);
    REG(HOST_BASE)=2u;     /* S1 identity, outside measured interval. */
    REG(HOST_BASE+4u)=1u;
    u32 tile_count=0, plane_bytes=(u32)w*(u32)h;
    for (int ty=0; ty<h; ty+=tile) {
        for (int tx=0; tx<w; tx+=tile) {
            int ymax=ty+tile<h ? ty+tile : h;
            int xmax=tx+tile<w ? tx+tile : w;
            for (u32 channel=0; channel<channels; ++channel) {
                u32 offset=channel*plane_bytes;
                sobel_tile_s1((volatile const u8 *)(IMAGE_BASE+offset),
                              (volatile u8 *)(OUTPUT_BASE+offset),
                              w,h,tx,ty,xmax,ymax);
            }
            REG(HOST_BASE+8u)=(u32)tx;
            REG(HOST_BASE+12u)=(u32)ty;
            REG(HOST_BASE+16u)=++tile_count;
        }
    }
    REG(HOST_BASE+4u)=2u;
    REG(HOST_BASE+24u)=1u;
    for (;;) { __asm__ volatile ("nop"); }
    return 0;
}
