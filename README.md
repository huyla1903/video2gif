# video2gif

Converts `.mov`/`.mp4` animations (e.g. web banners) to GIF at full resolution, optionally under a file-size limit.

## 💡 Motivation

Ad platforms and email clients often want banner animations as GIFs under a hard size cap (commonly 1 MB). Exporting a GIF straight from a video tool usually means guessing settings over and over, and most converters shrink the resolution first, which makes the banner look blurry.

video2gif automates that search. It never touches the resolution and gives up frame rate before colors, so the GIF keeps its full size and stays sharp. It also fixes an export bug where a video declares an odd size (e.g. 375×375) but only decodes 374 real columns, which would otherwise leave a garbage edge.

## 🚀 Quick Start

1. Install [Python 3](https://www.python.org/downloads/).
2. Install [ffmpeg](https://ffmpeg.org/download.html) and make sure `ffmpeg` and `ffprobe` are on your `PATH` (or in `C:\ffmpeg\bin` on Windows).
3. Convert a video:

```bash
python video2gif.py banner.mov
```

The GIF is written next to the input as `banner.gif`. There are no Python packages to install; the script only uses the standard library.

## 📖 Usage

**Drag and drop (Windows):** drop one or more videos onto `video2gif.bat`. It asks for a size limit in KB (e.g. `1000` for 1 MB); leave it blank to match the source.

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

### What it optimizes

With a size limit, quality is given up in this order:

1. **Resolution** is never reduced.
2. **File size** must fit the limit.
3. **Colors** (256 + bayer dithering) are kept as long as possible.
4. **Frame rate** is lowered first, in even steps (source fps / n: 25 → 12.5 → 8.33 → 6.25 …).

If the limit can't be reached, the smallest result is saved and the script suggests a shorter `--duration` or a lower `--min-fps`. Check the right/bottom edge of the output when the source has an odd size.

See [CLAUDE.md](CLAUDE.md) for implementation notes and size findings.

## 🤝 Contributing

### Clone the repo

```bash
git clone https://github.com/huyla1903/video2gif.git
cd video2gif
```

### Run it locally

There is no build step. With Python 3 and ffmpeg installed, run the script directly:

```bash
python video2gif.py --help
python video2gif.py --max-kb 1000 path/to/sample.mov
```

### Test your changes

There is no automated test suite yet. Before opening a pull request, convert a short sample video with and without `--max-kb` and check that:

- the GIF has the same resolution as the source,
- the file is under the limit when one is given,
- the right and bottom edges have no garbage pixels.

### Submit a pull request

If you'd like to contribute, please fork the repository and open a pull request to the `main` branch.
