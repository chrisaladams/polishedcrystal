/* Execution guard for the SameBoy backend: a C execution callback cheap enough to run on
 * every instruction. It records (does not stop) the first few suspicious executions:
 *   NOP_SLIDE   - 16+ consecutive NOPs executed above $8000 (running zeroed RAM)
 *   ILLEGAL     - an opcode the SM83 has no instruction for (hardware locks up)
 *   BAD_REGION  - code fetched from VRAM, OAM, the unusable area, or I/O registers
 * Build: cc -O2 -shared -fPIC -o execguard.so execguard.c
 */
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

void execguard_cb(void *gb, uint16_t pc, uint8_t op) {
    (void)gb;
    instructions++;
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
