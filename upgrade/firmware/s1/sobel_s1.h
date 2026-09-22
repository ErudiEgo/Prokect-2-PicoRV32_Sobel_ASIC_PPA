#ifndef SOBEL_S1_H
#define SOBEL_S1_H
/* Software-only horizontal window reuse. No MMIO or accelerator operation.
 * Preconditions: valid global image dimensions and nonempty in-bounds tile;
 * nonoverlapping input/output. Caller emits the tile event after all channels.
 * Volatile loads/stores match the S0 memory-access contract.
 */
static void sobel_tile_s1(volatile const unsigned char *image,
                          volatile unsigned char *output,
                          int w, int h, int tx, int ty, int xmax, int ymax)
{
    unsigned int row_offset = (unsigned int)ty * (unsigned int)w;
    for (int y = ty; y < ymax; ++y, row_offset += (unsigned int)w) {
        volatile const unsigned char *mid = image + row_offset;
        volatile const unsigned char *top = y > 0 ? mid - w : 0;
        volatile const unsigned char *bot = y + 1 < h ? mid + w : 0;
        volatile unsigned char *dst = output + row_offset;
        int a = (top && tx > 0) ? top[tx-1] : 0;
        int b = top ? top[tx] : 0;
        int d = tx > 0 ? mid[tx-1] : 0;
        int center = mid[tx];
        int f = (bot && tx > 0) ? bot[tx-1] : 0;
        int g = bot ? bot[tx] : 0;
        for (int x = tx; x < xmax; ++x) {
            int right = x + 1 < w;
            int c = (top && right) ? top[x+1] : 0;
            int e = right ? mid[x+1] : 0;
            int k = (bot && right) ? bot[x+1] : 0;
            int gx = c + 2*e + k - a - 2*d - f;
            int gy = f + 2*g + k - a - 2*b - c;
            if (gx < 0) gx = -gx;
            if (gy < 0) gy = -gy;
            int magnitude = gx + gy;
            dst[x] = (unsigned char)(magnitude > 255 ? 255 : magnitude);
            a = b; b = c;
            d = center; center = e;
            f = g; g = k;
        }
    }
}
#endif
