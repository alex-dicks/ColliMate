# ColliMate

A small Python utility for checking telescope collimation from a defocused star image.

If a star is deliberately defocused into a donut-shaped ring, the dark central hole should sit centered in the ring. If it is offset, the telescope is miscollimated. This script analyzes the image, finds the outer ring and the inner shadow, and reports the offset and direction.

## What it does

- Reads a defocused star image
- Detects the outer ring and central shadow
- Measures the offset between their centers
- Reports the offset in pixels and as a percentage of the ring radius
- Saves an annotated overlay image with fitted ellipses and centers

## Requirements

- Python 3
- OpenCV
- NumPy

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy opencv-python-headless
```

## Supported input formats

The script uses OpenCV's image loader, so it accepts common image files such as:

- `.jpg` / `.jpeg`
- `.png`
- `.bmp`
- `.tif` / `.tiff`

## Usage

Single image:

```bash
python3 collimate.py photo.jpg
```

Two images for comparison:

```bash
python3 collimate.py before.jpg after.jpg
```

The script will print:

- offset
- direction

It also writes an output file to visually inspect what the script has calculated:

```text
photo_fit.png
```

## Example output

```text
photo.jpg
  offset:    11px  (2.3% of ring radius)
  leaning:   left, down
  saved:     photo_fit.png
```

## Notes

This tool is intended for astrophotography and telescope collimation checks, especially with Mak and SCT telescopes. It is a quick image-analysis aid — read the raw percentages rather than a verdict, and use a second check (e.g. a Cheshire/autocollimator) to confirm before adjusting anything.

## License

This project is provided as-is for personal or hobby use.

## Author

Created for astronomy and telescope collimation work.
