/* Execution guard for the SameBoy backend: a C execution callback cheap enough to run on
 * every instruction. It records (does not stop) the first few suspicious executions:
 *   NOP_SLIDE   - 16+ consecutive NOPs executed above $8000 (running zeroed RAM)
 *   ILLEGAL     - an opcode the SM83 has no instruction for (hardware locks up)
 *   BAD_REGION  - code fetched from VRAM, OAM, the unusable area, or I/O registers
 * Build: cc -O2 -shared -fPIC -o execguard.so execguard.c
 */
#include <stddef.h>
#include <stdint.h>

#define MAX_EVENTS 32
enum { NOP_SLIDE = 1, ILLEGAL = 2, BAD_REGION = 3 };

typedef struct { uint16_t pc, prev; uint8_t op, kind; } event_t;

static event_t events[MAX_EVENTS];
static int count;
static uint64_t instructions;
static uint16_t prev_pc;
static int nop_run;

static int illegal(uint8_t op) {
    switch (op) {
    case 0xd3: case 0xdb: case 0xdd: case 0xe3: case 0xe4:
    case 0xeb: case 0xec: case 0xed: case 0xf4: case 0xfc: case 0xfd:
        return 1;
    }
    return 0;
}

static void record(uint16_t pc, uint8_t op, int kind) {
    if (count < MAX_EVENTS) {
        events[count].pc = pc; events[count].prev = prev_pc;
        events[count].op = op; events[count].kind = (uint8_t)kind;
    }
    count++;
}

/* Address watch: count executions of up to 32 chosen ROM addresses (bank -1 = any / bank 0 area).
 * Polled from Python instead of calling back per hit. hROMBank is read from HRAM ($ff87). */
#define MAX_WATCH 32
static struct { uint16_t pc; int bank; uint64_t hits; } watch[MAX_WATCH];
static int nwatch;
static const uint8_t *hram;          /* points at $ff80 */
/* ROM coverage bitmap: bit per (bank, offset) for bank 0..255 */
static uint8_t cover[256 * 0x4000 / 8];
static int cover_on;

void execguard_set_hram(const uint8_t *p) { hram = p; }

/* ---- AV monitors ------------------------------------------------------------------------
 * io: SameBoy's io_registers (GB_DIRECT_ACCESS_IO), for LY/STAT/LCDC without side effects.
 * VBlank workload: the PPU line (LY) at the moment the VBlank interrupt handler returns.
 * Lines 144-153 are inside VBlank; a value 0-143 means the handler ran into the next frame's
 * active display (an overrun), where VRAM writes are blocked on hardware.
 */
static const uint8_t *io;
static uint8_t irq_stack[8];
static int irq_depth;
static uint64_t vblank_ly_hist[154];
static uint64_t vblank_count;
void execguard_set_io(const uint8_t *p) { io = p; }
uint64_t av_vblank_count(void) { return vblank_count; }
uint64_t av_vblank_ly(int i) { return (i >= 0 && i < 154) ? vblank_ly_hist[i] : 0; }
void av_vblank_reset(void) { for (int i = 0; i < 154; i++) vblank_ly_hist[i] = 0; vblank_count = 0; }

static void track_irq(uint16_t pc, uint8_t op) {
    if (pc == 0x40 || pc == 0x48 || pc == 0x50 || pc == 0x58 || pc == 0x60) {
        if (irq_depth < 8) irq_stack[irq_depth++] = (uint8_t)pc;
    } else if (op == 0xd9 && irq_depth > 0) {          /* reti */
        uint8_t v = irq_stack[--irq_depth];
        if (v == 0x40 && io) {
            uint8_t ly = io[0x44];
            if (ly < 154) vblank_ly_hist[ly]++;
            vblank_count++;
        }
    }
}
int execguard_watch(uint16_t pc, int bank) {
    if (nwatch >= MAX_WATCH) return -1;
    watch[nwatch].pc = pc; watch[nwatch].bank = bank; watch[nwatch].hits = 0;
    return nwatch++;
}
uint64_t execguard_watch_hits(int i) { return (i >= 0 && i < nwatch) ? watch[i].hits : 0; }
void execguard_coverage(int on) { cover_on = on; }
const uint8_t *execguard_cover(void) { return cover; }
int execguard_cover_size(void) { return (int)sizeof(cover); }
void execguard_cover_clear(void) { for (size_t i = 0; i < sizeof(cover); i++) cover[i] = 0; }

void execguard_cb(void *gb, uint16_t pc, uint8_t op) {
    (void)gb;
    instructions++;
    if (pc < 0x100 || op == 0xd9) track_irq(pc, op);
    if (pc < 0x8000) {
        int bank = pc < 0x4000 ? 0 : (hram ? hram[0x07] : 1);   /* $ff87 - $ff80 */
        if (cover_on) {
            uint32_t bit = (uint32_t)bank * 0x4000u + (pc & 0x3fff);
            cover[bit >> 3] |= (uint8_t)(1u << (bit & 7));
        }
        for (int i = 0; i < nwatch; i++)
            if (watch[i].pc == pc && (watch[i].bank < 0 || watch[i].bank == bank)) watch[i].hits++;
    }
    if (illegal(op)) record(pc, op, ILLEGAL);
    if ((pc >= 0x8000 && pc < 0xa000) || (pc >= 0xfe00 && pc < 0xff80)) record(pc, op, BAD_REGION);
    if (op == 0x00 && pc >= 0x8000) {
        if (++nop_run == 16) record(pc, op, NOP_SLIDE);
    } else {
        nop_run = 0;
    }
    prev_pc = pc;
}

void *execguard_fn(void) { return (void *)execguard_cb; }
int execguard_count(void) { return count; }
uint64_t execguard_instructions(void) { return instructions; }
int execguard_get(int i, uint16_t *pc, uint16_t *prev, uint8_t *op, uint8_t *kind) {
    if (i < 0 || i >= count || i >= MAX_EVENTS) return 0;
    *pc = events[i].pc; *prev = events[i].prev; *op = events[i].op; *kind = events[i].kind;
    return 1;
}
void execguard_reset(void) { count = 0; nop_run = 0; instructions = 0; }


/* ---- PPU access timing --------------------------------------------------------------------
 * Install as the write callback. A CPU write to VRAM during PPU mode 3, or to OAM during modes
 * 2-3, with the LCD on, is dropped by real hardware. Recorded, never blocked.
 */
#define MAX_ACCESS 64
typedef struct { uint16_t addr, pc; uint8_t value, mode, ly, kind; } access_t;
static access_t accesses[MAX_ACCESS];
static int access_count;
static uint64_t vram_bad, oam_bad, vram_writes, oam_writes;

int av_write_cb(void *gb, uint16_t addr, uint8_t value) {
    (void)gb;
    int is_vram = addr >= 0x8000 && addr < 0xa000;
    int is_oam = addr >= 0xfe00 && addr < 0xfea0;
    if (!is_vram && !is_oam) return 1;
    if (is_vram) vram_writes++; else oam_writes++;
    if (!io || !(io[0x40] & 0x80)) return 1;            /* LCD off: everything is accessible */
    uint8_t mode = io[0x41] & 3;
    int bad = is_vram ? (mode == 3) : (mode == 2 || mode == 3);
    if (bad) {
        if (is_vram) vram_bad++; else oam_bad++;
        if (access_count < MAX_ACCESS) {
            access_t *a = &accesses[access_count];
            a->addr = addr; a->value = value; a->mode = mode; a->ly = io[0x44];
            a->pc = prev_pc; a->kind = is_vram ? 1 : 2;
        }
        access_count++;
    }
    return 1;
}
void *av_write_fn(void) { return (void *)av_write_cb; }
uint64_t av_vram_writes(void) { return vram_writes; }
uint64_t av_oam_writes(void) { return oam_writes; }
uint64_t av_vram_bad(void) { return vram_bad; }
uint64_t av_oam_bad(void) { return oam_bad; }
int av_access_count(void) { return access_count; }
int av_access_get(int i, uint16_t *addr, uint16_t *pc, uint8_t *value, uint8_t *mode, uint8_t *ly, uint8_t *kind) {
    if (i < 0 || i >= access_count || i >= MAX_ACCESS) return 0;
    *addr = accesses[i].addr; *pc = accesses[i].pc; *value = accesses[i].value;
    *mode = accesses[i].mode; *ly = accesses[i].ly; *kind = accesses[i].kind;
    return 1;
}
void av_access_reset(void) { access_count = 0; vram_bad = oam_bad = vram_writes = oam_writes = 0; }

/* ---- Audio capture ------------------------------------------------------------------------ */
#include <stdlib.h>
typedef struct { int16_t left, right; } sample_t;
static sample_t *audio;
static size_t audio_cap, audio_n;
void av_audio_init(size_t cap) {
    free(audio);
    audio = (sample_t *)malloc(cap * sizeof(sample_t));
    audio_cap = audio ? cap : 0; audio_n = 0;
}
void av_audio_cb(void *gb, sample_t *s) {
    (void)gb;
    if (audio_n < audio_cap) audio[audio_n++] = *s;
}
void *av_audio_fn(void) { return (void *)av_audio_cb; }
size_t av_audio_count(void) { return audio_n; }
const int16_t *av_audio_data(void) { return (const int16_t *)audio; }
void av_audio_reset(void) { audio_n = 0; }
