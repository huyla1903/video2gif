# video2gif

Converts .mov/.mp4 banner animations to GIF. ffmpeg/ffprobe live in `C:\ffmpeg\bin` (prepend it to PATH if not found).

## Tools

- `video2gif.py`: the single converter script.
  ```
  python video2gif.py file1.mov [file2.mp4 ...] [--max-kb 1000] [--min-fps 4] [--start S] [--duration S] [--outdir DIR]
  ```
  - No `--max-kb`: matches the source (declared resolution, source fps, 256 colors, no denoise).
  - With `--max-kb`: searches as described in the priorities below.
- `video2gif.bat`: drag-and-drop wrapper. It asks for a size limit in KB; leave it blank to match the source.

## Conversion priorities (user-defined, in order)

1. **Resolution**: always keep the source's declared size (e.g. 375x375). Never scale down.
2. **File size**: must be under the limit when one is given (usually 1 MB = `--max-kb 1000`).
3. **Colors**: keep 256-color palette + bayer dithering as long as possible.
4. **Frame rate**: the first thing to give up. Tried as source_fps/n (25 → 12.5 → 8.33 → 6.25 …) so frames are evenly spaced and GIF delays are whole centiseconds.

With a limit, the script searches in exactly this order: for each color count (then dither mode), it lowers fps until the GIF fits.

## Odd-resolution edge bug

Some exports declare an odd size (e.g. 375x375 ProRes 4:2:2) but only decode 374 real columns, so forcing 375 creates a garbage edge column. The script detects the real decodable size (crop at the declared size; ffmpeg clamps it, read back from the PPM header), crops to it, and then rebuilds the declared size with `pad` + `fillborders=mode=smear` (replicating the last good column/row). Always visually check the right/bottom edge of the output.

## Size findings

- A temporal-only denoise (`hqdn3d=0:0:6:6`) roughly halves GIF size on grainy sources without softening edges. It's only applied in size-limited mode.
- `stats_mode=diff` + `diff_mode=rectangle` help; `dither=none` is only ~5% smaller than bayer, so it's not worth the banding.
- Reference: the 375x375, 9 s, 25 fps Prisfest banner → 375x375, 6.25 fps, 256 colors, bayer = 928 KB (1 MB limit). With no limit it's 6.2 MB at 25 fps.
