# video2gif

Converts `.mov`/`.mp4` animations (e.g. web banners) to GIF at full resolution, optionally under a file-size limit.

## Requirements

- Python 3
- ffmpeg and ffprobe, on `PATH` or in `C:\ffmpeg\bin`

## Usage

**Drag and drop:** drop one or more videos onto `video2gif.bat`. It asks for a size limit in KB (e.g. `1000` for 1 MB); leave it blank to match the source.

**Command line:**

```bash
python video2gif.py file1.mov file2.mp4
```

```bash
python video2gif.py --max-kb 1000 --start 2 --duration 5 --outdir out file.mov
```

| Option | Meaning |
|---|---|
| `--max-kb N` | Keep the GIF under N KB. Without it, the GIF matches the source (resolution, fps, 256 colors). |
| `--min-fps N` | Lowest frame rate tried before colors are reduced (default 4). |
| `--start S`, `--duration S` | Trim the input (seconds). |
| `--outdir DIR` | Where to write the GIFs (default: next to the input). |

## What it optimizes

With a size limit, quality is given up in this order:

1. **Resolution** is never reduced.
2. **File size** must fit the limit.
3. **Colors** (256 + bayer dithering) are kept as long as possible.
4. **Frame rate** is lowered first, in even steps (source fps / n: 25 → 12.5 → 8.33 → 6.25 …).

It also fixes a common export bug where a video declares an odd size (e.g. 375×375) but only decodes 374 real columns, which would otherwise leave a garbage edge. Check the right/bottom edge of the output anyway.

See [CLAUDE.md](CLAUDE.md) for implementation notes and size findings.
