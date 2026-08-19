#!/usr/bin/env bash
# Kids CUDA probe. Stamp real numbers or NONE. Never invent a CUDA score.
#   ./scripts/kids cuda
# GPU kid (nvidia-smi + nvcc): writes H2D/D2H/D2D.
# This cloud is CPU-only — expect CUDA: NONE.
set -euo pipefail
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$ROOT"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ID="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p bus/kids/stamps
STAMP="bus/kids/stamps/CUDA_${ID}.txt"
NOWFILE="bus/kids/CUDA_NOW.txt"

GPU="NONE"
DEV="absent"
SMI="absent"
NVCC="absent"
CUDA_H2D_GBs="NONE"
CUDA_H2D_MTs="NONE"
CUDA_D2H_GBs="NONE"
CUDA_D2H_MTs="NONE"
CUDA_D2D_GBs="NONE"
CUDA_D2D_MTs="NONE"
CUDA_NOTE="no GPU on this box"
HOST_GBs="NONE"
HOST_MTs="NONE"

if ls /dev/nvidia* >/dev/null 2>&1; then
  DEV="present"
fi
if command -v nvidia-smi >/dev/null 2>&1; then
  SMI="$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -1 | tr -s ' ' || true)"
  if [ -n "$SMI" ]; then
    GPU="PRESENT"
  fi
fi
if command -v nvcc >/dev/null 2>&1; then
  NVCC="$(nvcc --version 2>/dev/null | tail -1 | tr -s ' ' || echo present)"
fi

# Host memcpy control — same MT/s = GB/s * 1024 as authority 23072. NOT CUDA.
HOST_LINE="$(python3 - <<'PY'
import time
n = 256 * 1024 * 1024
reps = 8
a = bytearray(n)
b = bytearray(n)
b[:] = a
t0 = time.perf_counter()
for _ in range(reps):
    b[:] = a
dt = time.perf_counter() - t0
if dt <= 0:
    print("NONE NONE")
else:
    gbs = (n * reps) / dt / 1e9
    print(f"{gbs:.3f} {gbs * 1024:.0f}")
PY
)"
HOST_GBs="$(echo "$HOST_LINE" | awk '{print $1}')"
HOST_MTs="$(echo "$HOST_LINE" | awk '{print $2}')"

if [ "$GPU" = "PRESENT" ] && [ "$NVCC" != "absent" ]; then
  TMP="$(mktemp -d)"
  set +e
  nvcc -O2 "$ROOT/scripts/kids-cuda-bandwidth.cu" -o "$TMP/kids-cuda-bw" >/tmp/kids-cuda-nvcc.log 2>&1
  COMPILE=$?
  set -e
  if [ "$COMPILE" -eq 0 ]; then
    set +e
    OUT="$("$TMP/kids-cuda-bw" 2>/tmp/kids-cuda-run.log)"
    RUN=$?
    set -e
    if [ "$RUN" -eq 0 ]; then
      CUDA_H2D_GBs="$(echo "$OUT" | awk '/CUDA_H2D_GBs/{print $2}')"
      CUDA_H2D_MTs="$(echo "$OUT" | awk '/CUDA_H2D_MTs/{print $2}')"
      CUDA_D2H_GBs="$(echo "$OUT" | awk '/CUDA_D2H_GBs/{print $2}')"
      CUDA_D2H_MTs="$(echo "$OUT" | awk '/CUDA_D2H_MTs/{print $2}')"
      CUDA_D2D_GBs="$(echo "$OUT" | awk '/CUDA_D2D_GBs/{print $2}')"
      CUDA_D2D_MTs="$(echo "$OUT" | awk '/CUDA_D2D_MTs/{print $2}')"
      CUDA_NOTE="nvcc bench PASS"
    else
      CUDA_NOTE="GPU present · bench RUN fail (see /tmp/kids-cuda-run.log). No invented score."
    fi
  else
    CUDA_NOTE="GPU present · nvcc COMPILE fail (see /tmp/kids-cuda-nvcc.log). No invented score."
  fi
  rm -rf "$TMP"
elif [ "$GPU" = "PRESENT" ]; then
  CUDA_NOTE="GPU present · nvcc absent. Cannot invent a CUDA score."
else
  CUDA_NOTE="no GPU (nvidia-smi /dev/nvidia*). CUDA: NONE. Host memcpy is not CUDA."
fi

{
  echo "CUDA NUMBERS  ${NOW}  kids · box=$(hostname) user=$(id -un)"
  echo "NEW CUDA: ${CUDA_H2D_MTs}"
  echo "gpu: ${GPU}"
  echo "dev_nvidia: ${DEV}"
  echo "smi: ${SMI}"
  echo "nvcc: ${NVCC}"
  echo "CUDA_H2D_GBs ${CUDA_H2D_GBs}"
  echo "CUDA_H2D_MTs ${CUDA_H2D_MTs}"
  echo "CUDA_D2H_GBs ${CUDA_D2H_GBs}"
  echo "CUDA_D2H_MTs ${CUDA_D2H_MTs}"
  echo "CUDA_D2D_GBs ${CUDA_D2D_GBs}"
  echo "CUDA_D2D_MTs ${CUDA_D2D_MTs}"
  echo "HOST_MEMCPY_GBs ${HOST_GBs}   # NOT CUDA · same unit as 23072 (GB/s * 1024 = MT/s)"
  echo "HOST_MEMCPY_MTs ${HOST_MTs}   # NOT CUDA"
  echo "note: ${CUDA_NOTE}"
  echo
  echo "KNOWN SPEAK (not CUDA — authority host memcpy, test 2026-08-19T00:39:57Z)"
  echo "23072 MT/s  vs  9000  (2.56×) · memcpy 22.531 GB/s · pack 14.034 GB/s (14371 MT/s)"
  echo
  echo "NEXT"
  echo "GPU kid: ./scripts/kids cuda   then commit this file."
  echo "Do not curl-grade. Do not speak HOST as CUDA. Do not invent."
  echo
  echo "Word: CUDA ${CUDA_H2D_MTs} · HOST ${HOST_MTs} · 23072 IS MEMCPY"
} | tee "$STAMP" > "$NOWFILE"

echo "CUDA stamp ${NOW}"
echo "file: ${NOWFILE}"
echo "NEW CUDA: ${CUDA_H2D_MTs}"
