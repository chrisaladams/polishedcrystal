/* Atomic helpers for the lockstep link cable shared between two processes. */
#include <stdint.h>
#include <sched.h>
static inline uint64_t lk_get64(uint8_t *p) { return __atomic_load_n((uint64_t *)p, __ATOMIC_ACQUIRE); }
static inline void lk_set64(uint8_t *p, uint64_t v) { __atomic_store_n((uint64_t *)p, v, __ATOMIC_RELEASE); }
static inline uint8_t lk_get8(uint8_t *p) { return __atomic_load_n(p, __ATOMIC_ACQUIRE); }
static inline void lk_set8(uint8_t *p, uint8_t v) { __atomic_store_n(p, v, __ATOMIC_RELEASE); }
static inline void lk_yield(void) { sched_yield(); }
static inline uint8_t *lk_ptr(uint64_t a) { return (uint8_t *)(uintptr_t)a; }
/* Optional line noise on bytes this side receives: slot+14 (u16) N flips one
 * random bit in about 1 of every N bytes; slot+16 holds the generator state,
 * slot+20 counts flips. */
static inline uint8_t lk_noise(uint8_t *slot, uint8_t b) {
    uint16_t n = *(volatile uint16_t *)(slot + 14);
    if (!n) return b;
    uint32_t s = *(volatile uint32_t *)(slot + 16) * 1103515245u + 12345u;
    if (((s >> 16) % n) == 0) {
        s = s * 1103515245u + 12345u;
        b ^= (uint8_t)(1u << ((s >> 16) & 7));
        *(volatile uint32_t *)(slot + 20) += 1;
    }
    *(volatile uint32_t *)(slot + 16) = s;
    return b;
}
