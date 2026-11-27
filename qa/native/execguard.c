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
