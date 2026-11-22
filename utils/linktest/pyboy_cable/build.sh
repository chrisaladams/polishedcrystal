#!/bin/sh
# Build a copy of the installed PyBoy (2.9) whose shared-memory serial link is
# a lockstep cable with real clock semantics (see serial.py), for linktest.py.
#
#   sh utils/linktest/pyboy_cable/build.sh OUTDIR
#   PYTHONPATH=OUTDIR python3 utils/linktest/linktest.py A.sav B.sav
#
# Needs Cython (pip install cython) and a C compiler.
set -e
here=$(cd "$(dirname "$0")" && pwd)
out=${1:?usage: build.sh OUTDIR}
src=$(python3 -c 'import os, pyboy; print(os.path.dirname(pyboy.__file__))')
rm -rf "$out/pyboy"
mkdir -p "$out"
cp -r "$src" "$out/pyboy"
cp "$here/serial.py" "$here/serial.pxd" "$here/linkhelp.h" "$out/pyboy/core/"
rm -f "$out/pyboy/core/serial.c" "$out"/pyboy/core/serial.cpython-*.so
cd "$out"
cythonize -3 -i -X infer_types=True,boundscheck=False,wraparound=False,cdivision=True pyboy/core/serial.py
echo "built $out/pyboy"
