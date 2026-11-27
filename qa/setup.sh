#!/bin/sh
# Installs the QA toolchain. Idempotent: each step is skipped if its result exists.
#
#   sh qa/setup.sh            everything
#   sh qa/setup.sh rgbds      just one step: rgbds | pyboy | sameboy | gearboy
#
# Everything is built from public git repositories at pinned versions into $GBDEV
# (default ~/gbdev); RGBDS goes to /opt/rgbds and SDL3 to /opt/sdl3 (override with
# RGBDS_PREFIX / SDL3_PREFIX). Needs: git, cmake, make, gcc, g++, bison, libpng-dev, pkg-config.
#
# Versions used for the numbers in docs/qa-report.md:
#   RGBDS 1.0.4, PyBoy 2.9.0, SameBoy (see `git -C $GBDEV/SameBoy rev-parse HEAD` in each report),
#   Gearboy 3.8.x, SDL3 3.2.8.
# BGB (closed source, Windows) and Emulicious (Java, emulicious.net) are NOT installed here:
# see docs/qa-report.md "Tools not available".
set -eu
GBDEV=${GBDEV:-$HOME/gbdev}
RGBDS_PREFIX=${RGBDS_PREFIX:-/opt/rgbds}
SDL3_PREFIX=${SDL3_PREFIX:-/opt/sdl3}
RGBDS_TAG=${RGBDS_TAG:-v1.0.4}
SDL3_TAG=${SDL3_TAG:-release-3.2.8}
JOBS=${JOBS:-$(nproc 2>/dev/null || echo 2)}
mkdir -p "$GBDEV"

clone() { # url dir [tag]
    [ -d "$2/.git" ] && return 0
    if [ -n "${3:-}" ]; then GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --branch "$3" "$1" "$2"
    else GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "$1" "$2"; fi
}

step_rgbds() {
    [ -x "$RGBDS_PREFIX/bin/rgbasm" ] && "$RGBDS_PREFIX/bin/rgbasm" --version | grep -q "${RGBDS_TAG#v}" && { echo "rgbds ok"; return; }
    clone https://github.com/gbdev/rgbds "$GBDEV/rgbds" "$RGBDS_TAG"
    (cd "$GBDEV/rgbds" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$RGBDS_PREFIX" >/dev/null \
        && cmake --build build -j"$JOBS" && cmake --install build)
}

step_pyboy() {
    python3 -c "import pyboy" 2>/dev/null && { echo "pyboy ok"; return; }
    python3 -m pip install 'pyboy==2.9.0' pillow numpy
}

step_sameboy() {
    [ -f "$GBDEV/SameBoy/build/lib/libsameboy.so" ] && { echo "sameboy ok"; return; }
    clone https://github.com/LIJI32/SameBoy "$GBDEV/SameBoy"
    (cd "$GBDEV/SameBoy" && PATH="$RGBDS_PREFIX/bin:$PATH" make -j"$JOBS" tester lib CONF=release)
}

step_gearboy() {
    [ -x "$GBDEV/Gearboy/platforms/linux/gearboy" ] && { echo "gearboy ok"; return; }
    if [ ! -f "$SDL3_PREFIX/lib/pkgconfig/sdl3.pc" ]; then   # Gearboy needs SDL3 (not in Ubuntu 24.04)
        clone https://github.com/libsdl-org/SDL "$GBDEV/SDL3" "$SDL3_TAG"
        (cd "$GBDEV/SDL3" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$SDL3_PREFIX" \
            -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF >/dev/null && cmake --build build -j"$JOBS" && cmake --install build)
    fi
    clone https://github.com/drhelius/Gearboy "$GBDEV/Gearboy"
    (cd "$GBDEV/Gearboy/platforms/linux" && PKG_CONFIG_PATH="$SDL3_PREFIX/lib/pkgconfig" LD_LIBRARY_PATH="$SDL3_PREFIX/lib" make -j"$JOBS")
}

if [ $# -eq 0 ]; then set -- rgbds pyboy sameboy gearboy; fi
for s in "$@"; do "step_$s"; done
echo "done. Put $RGBDS_PREFIX/bin on PATH, then: make qa-regression"
