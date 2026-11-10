#!/usr/bin/env python3
"""
@title        video2gif
@version      0.1.0
@author       La Gia Huy
@since        2026-10-05
@updated      2026-10-05
@engine       Python 3
@target       Windows; ffmpeg
@about        Convert .mov/.mp4 files to GIF at full resolution, optionally under a size limit.

              Without --max-kb: output matches the source (declared resolution, source fps,
              256 colors, no denoise).

              With --max-kb, priority order (see CLAUDE.md):
                  1. resolution  - always kept at the source's declared size
                  2. file size   - must be <= --max-kb
                  3. colors      - palette size, then dithering
                  4. frame rate  - lowered first

              Frame rates are tried as source_fps / n (e.g. 25, 12.5, 8.33, 6.25 ...) so
              frames stay evenly spaced and GIF delays land on whole centiseconds.

              Edge fix: some exports declare e.g. 375x375 but only decode 374 real columns;
              forcing the declared size fabricates a garbage edge pixel. We detect the real
              decodable size, crop to it, and smear the last good column/row back out to
              the declared size.

              Usage:
                  python video2gif.py file1.mov file2.mp4 ...
                  python video2gif.py --max-kb 1000 file.mov
                  python video2gif.py --max-kb 1000 --start 2 --duration 5 file.mov

              Requires ffmpeg/ffprobe on PATH or in C:\\ffmpeg\\bin.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

COLORS = [256, 192, 128, 96, 64]
DITHERS = ["bayer:bayer_scale=5", "none"]  # better-looking first
# Temporal-only denoise: removes film grain that otherwise changes every
# pixel every frame (roughly halves GIF size) without softening edges.
# Only used when a size limit is set.
DENOISE = "hqdn3d=0:0:6:6"


def find_exe(name):
    exe = shutil.which(name)
    if exe:
        return exe
    fallback = Path(r"C:\ffmpeg\bin") / f"{name}.exe"
    if fallback.exists():
        return str(fallback)
    sys.exit(f"'{name}' not found. Install ffmpeg or put it in C:\\ffmpeg\\bin")


def probe(ffprobe, path):
    out = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "csv=p=0:s=x", path],
        capture_output=True, text=True, check=True).stdout.strip()
    w, h, rate = out.split("x")
    return int(w), int(h), Fraction(rate)


def real_dimension(ffmpeg, path, axis, declared):
    """Crop at the declared size along one axis; ffmpeg silently clamps to
    the real decodable size, which we read back from the PPM header."""
    vf = f"crop={declared}:2:0:0" if axis == "w" else f"crop=2:{declared}:0:0"
    r = subprocess.run(
        [ffmpeg, "-v", "error", "-i", path, "-vf", vf, "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "ppm", "-pix_fmt", "rgb24", "-"],
        capture_output=True)
    if not r.stdout:
        return declared
    w, h = r.stdout.split(b"\n", 3)[1].split()
    return int(w) if axis == "w" else int(h)


def encode(ffmpeg, src, dst, geom, fps, colors, dither, denoise, start, duration):
    dw, dh, rw, rh = geom
    vf = f"fps={fps},"
    if denoise:
        vf += f"{DENOISE},"
    vf += f"crop={rw}:{rh}:0:0,format=rgb24"
    if (rw, rh) != (dw, dh):
        vf += (f",pad={dw}:{dh}:0:0,"
               f"fillborders=right={dw - rw}:bottom={dh - rh}:mode=smear")
    vf += (f",split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
           f"[b][p]paletteuse=dither={dither}:diff_mode=rectangle")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if start:
        cmd += ["-ss", str(start)]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-i", str(src), "-an", "-filter_complex", vf, "-loop", "0", str(dst)]
    subprocess.run(cmd, check=True)
    return os.path.getsize(dst)


def convert(ffmpeg, ffprobe, src, args):
    print(f"\n=== {src.name} ===")
    outdir = Path(args.outdir) if args.outdir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / (src.stem + ".gif")

    dw, dh, src_fps = probe(ffprobe, str(src))
    rw = real_dimension(ffmpeg, str(src), "w", dw)
    rh = real_dimension(ffmpeg, str(src), "h", dh)
    geom = (dw, dh, rw, rh)
    limit_txt = f"<= {args.max_kb} KB" if args.max_kb else "no size limit"
    print(f"Source {dw}x{dh} @ {float(src_fps):g} fps, {limit_txt}")
    if (rw, rh) != (dw, dh):
        print(f"  Real decodable frame is {rw}x{rh} -> rebuilding edge to {dw}x{dh}")

    if not args.max_kb:
        size = encode(ffmpeg, src, output, geom, src_fps, 256, DITHERS[0],
                      False, args.start, args.duration)
        print(f"Done: {output} ({size / 1024:.1f} KB, {dw}x{dh}, "
              f"{float(src_fps):.2f} fps, 256 colors)")
        return True

    limit = args.max_kb * 1024
    fps_steps = []
    n = 1
    while src_fps / n >= args.min_fps:
        fps_steps.append(src_fps / n)
        n += 1

    tmpdir = tempfile.mkdtemp()
    tmp = os.path.join(tmpdir, "out.gif")
    best = None
    try:
        for colors in COLORS:
            for dither in DITHERS:
                for fps in fps_steps:
                    size = encode(ffmpeg, src, tmp, geom, fps, colors, dither,
                                  True, args.start, args.duration)
                    print(f"  colors={colors:3d} dither={dither.split(':')[0]:5s} "
                          f"fps={float(fps):5.2f} -> {size / 1024:7.1f} KB")
                    if best is None or size < best:
                        best = size
                        shutil.copyfile(tmp, output)
                    if size <= limit:
                        print(f"Done: {output} ({size / 1024:.1f} KB, {dw}x{dh}, "
                              f"{float(fps):.2f} fps, {colors} colors, dither={dither})")
                        return True
        print(f"Could not reach {args.max_kb} KB. Smallest result saved: "
              f"{output} ({best / 1024:.1f} KB). Try --duration or lower --min-fps.")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Video -> GIF at full resolution, optional size limit")
    ap.add_argument("files", nargs="+", help="video files to convert")
    ap.add_argument("--max-kb", type=int, default=None,
                    help="size limit in KB (e.g. 1000 = 1 MB); omit to match source settings")
    ap.add_argument("--min-fps", type=float, default=4,
                    help="lowest frame rate before reducing colors (default 4)")
    ap.add_argument("--start", type=float, help="start time in seconds")
    ap.add_argument("--duration", type=float, help="clip length in seconds")
    ap.add_argument("--outdir", help="output directory (default: next to input)")
    args = ap.parse_args()

    ffmpeg, ffprobe = find_exe("ffmpeg"), find_exe("ffprobe")
    ok = True
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"Skipping (not found): {f}")
            ok = False
            continue
        try:
            ok &= convert(ffmpeg, ffprobe, p, args)
        except Exception as e:
            print(f"  ERROR converting {f}: {e}")
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
