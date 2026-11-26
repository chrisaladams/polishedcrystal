#!/usr/bin/env python3
"""Make and apply BPS patches (byuu's format, as Floating IPS and ROM Patcher
JS read it: see their bps_spec.md).

The encoder writes runs of SourceRead (bytes the same at the same offset) and
TargetRead (new bytes), with SourceCopy for long runs found elsewhere in the
source (a moved bank). The decoder is written separately from the encoder,
from the specification, and checks the source, target and patch CRC-32s, so
`make` can check every patch by applying it.

Usage:
  python3 utils/release/bps.py make SOURCE TARGET PATCH
  python3 utils/release/bps.py apply SOURCE PATCH OUTPUT
"""
import sys
import zlib

MIN_COPY = 32  # a shorter match isn't worth a SourceCopy over a TargetRead


def _number(n):
    out = bytearray()
    while True:
        x = n & 0x7f
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def make(source, target):
    out = bytearray(b'BPS1')
    out += _number(len(source)) + _number(len(target)) + _number(0)
    # index of source blocks for SourceCopy
    BLOCK = 16
    index = {}
    for i in range(0, len(source) - BLOCK + 1, BLOCK):
        index.setdefault(source[i:i + BLOCK], i)
    source_rel = 0  # the decoder's source-relative offset
    pending = bytearray()

    def flush():
        if pending:
            out.extend(_number(((len(pending) - 1) << 2) | 1))
            out.extend(pending)
            pending.clear()

    i, n = 0, len(target)
    while i < n:
        # same bytes at the same offset
        j = i
        while j < n and j < len(source) and source[j] == target[j]:
            j += 1
        if j - i >= 4:
            flush()
            out.extend(_number(((j - i - 1) << 2) | 0))
            i = j
            continue
        # a long run elsewhere in the source
        block = target[i:i + BLOCK]
        k = index.get(block) if len(block) == BLOCK else None
        if k is not None:
            m = 0
            while i + m < n and k + m < len(source) and source[k + m] == target[i + m]:
                m += 1
            if m >= MIN_COPY:
                flush()
                out.extend(_number(((m - 1) << 2) | 2))
                d = k - source_rel
                out.extend(_number((abs(d) << 1) | (1 if d < 0 else 0)))
                source_rel = k + m
                i += m
                continue
        pending.append(target[i])
        i += 1
    flush()
    out += zlib.crc32(source).to_bytes(4, 'little')
    out += zlib.crc32(target).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)


def apply(source, patch):
    """Decode by the specification, independently of make()."""
    if patch[:4] != b'BPS1':
        raise ValueError('not a BPS patch')
    end = len(patch) - 12
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], 'little'):
        raise ValueError('patch checksum')
    if zlib.crc32(source) != int.from_bytes(patch[-12:-8], 'little'):
        raise ValueError('this is not the source ROM the patch is for')
    pos = 4

    def number():
        nonlocal pos
        data, shift = 0, 1
        while True:
            x = patch[pos]
            pos += 1
            data += (x & 0x7f) * shift
            if x & 0x80:
                return data
            shift <<= 7
            data += shift

    src_size, tgt_size, meta = number(), number(), number()
    pos += meta
    if src_size != len(source):
        raise ValueError('source size')
    target = bytearray(tgt_size)
    out = src_rel = tgt_rel = 0
    while pos < end:
        word = number()
        cmd, length = word & 3, (word >> 2) + 1
        if cmd == 0:  # SourceRead
            target[out:out + length] = source[out:out + length]
        elif cmd == 1:  # TargetRead
            target[out:out + length] = patch[pos:pos + length]
            pos += length
        elif cmd == 2:  # SourceCopy
            d = number()
            src_rel += -(d >> 1) if d & 1 else d >> 1
            target[out:out + length] = source[src_rel:src_rel + length]
            src_rel += length
        else:  # TargetCopy, byte by byte (it may overlap itself)
            d = number()
            tgt_rel += -(d >> 1) if d & 1 else d >> 1
            for _ in range(length):
                target[out] = target[tgt_rel]
                out += 1
                tgt_rel += 1
            continue
        out += length
    if out != tgt_size:
        raise ValueError('target size')
    if zlib.crc32(target) != int.from_bytes(patch[-8:-4], 'little'):
        raise ValueError('target checksum')
    return bytes(target)


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ('make', 'apply'):
        sys.exit(__doc__)
    a, b = open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read()
    if sys.argv[1] == 'make':
        patch = make(a, b)
        if apply(a, patch) != b:
            sys.exit('the patch does not reproduce the target')
        open(sys.argv[4], 'wb').write(patch)
    else:
        open(sys.argv[4], 'wb').write(apply(a, b))


if __name__ == '__main__':
    main()
