#!/usr/bin/env python3
"""
collimate.py

Checks a defocused-star photo for collimation error, plus a rough
astigmatism estimate.

Usage:
    python3 collimate.py photo.jpg
    python3 collimate.py photo1.jpg photo2.jpg  # report on both
    python3 collimate.py a_folder_of_photos/    # processes every photo inside

Needs: pip install opencv-python-headless numpy
"""

import sys
import os
import cv2
import numpy as np

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


def expand_paths(args):
    """Turns files/folders into a flat list of photo pathss, sorted by name."""
    paths = []
    for arg in args:
        if os.path.isdir(arg):
            found = sorted(
                os.path.join(arg, f)
                for f in os.listdir(arg)
                if f.lower().endswith(IMAGE_EXTS)
            )
            if not found:
                sys.exit(f"No photos found in {arg}/")
            paths.extend(found)
        else:
            paths.append(arg)
    return paths

def find_the_two_circles(path):
    """Load the photo and find the outer ring + inner shadow as ellipses."""
    img = cv2.imread(path)
    if img is None:
        sys.exit(f"Couldn't open {path} — check the path.")

    # Use lumiance channel.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    gray = cv2.GaussianBlur(gray, (9, 9), 0)  # smooth out sensor noise a bit

    # Convert to black and white so the donut edges are easier to trace.
    _, bw = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    shapes, _ = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

    if len(shapes) < 2:
        sys.exit(
            "Only found one shape, not a ring + a hole. Make sure the star "
            "is defocused into a clear donut and try again."
        )

    # Biggest shape = outer ring. Second biggest = inner ring.
    shapes = sorted(shapes, key=cv2.contourArea, reverse=True)
    outer, inner = shapes[0], shapes[1]

    # fitEllipse gives us a clean center point for each, even if the
    # photo is a bit noisy or slightly egg-shaped. It needs >= 5 points.
    if len(outer) < 5 or len(inner) < 5:
        sys.exit(
            "The ring or the shadow was too small/noisy to fit."
        )
    return img, cv2.fitEllipse(outer), cv2.fitEllipse(inner)


def check_collimation(outer, inner):
    """Compare the two circle centers."""
    (ox, oy), (ow, oh), _ = outer
    (ix, iy), (iw, ih), _ = inner

    dx, dy = ox - ix, oy - iy
    offset_px = (dx**2 + dy**2) ** 0.5
    ring_radius = (ow + oh) / 4
    offset_pct = 100 * offset_px / ring_radius if ring_radius else 0.0

    if offset_pct < 0.5:
        direction = "centered"
    else:
        left_right = "left" if dx > 0 else "right" if dx < 0 else "center"
        up_down = "up" if dy > 0 else "down" if dy < 0 else "center"

        if left_right == "center" and up_down == "center":
            direction = "centered"
        elif left_right == "center":
            direction = up_down
        elif up_down == "center":
            direction = left_right
        else:
            direction = f"{left_right}, {up_down}"

    return {
        "offset_px": offset_px,
        "offset_pct": offset_pct,
        "direction": direction,
    }


def check_astigmatism(outer):
    """Astigmatism shows up as the outer ring being stretched into an oval
    instead of a circle. Compare the fitted ellipse's two axes."""
    (_, _), (ow, oh), angle = outer

    major, minor = max(ow, oh), min(ow, oh)
    astig_pct = 100 * (major - minor) / major if major else 0.0

    return {
        "astig_pct": astig_pct,
        "axis_angle": angle,
    }


def draw_overlay(img, outer, inner, result, astig, out_path):
    """Save a copy of the photo with the two fitted circles and the
    measured results drawn on it."""
    vis = img.copy()
    cv2.ellipse(vis, outer, (0, 255, 0), 4)   # green = outer ring
    cv2.ellipse(vis, inner, (255, 255, 0), 4)  # yellow = the shadow
    cv2.circle(vis, tuple(map(int, outer[0])), 8, (0, 255, 0), -1)
    cv2.circle(vis, tuple(map(int, inner[0])), 8, (255, 255, 0), -1)

    # crop
    cx, cy = map(int, outer[0])
    half = int(max(outer[1]) / 2) + 150
    y0, y1 = max(0, cy - half), min(vis.shape[0], cy + half)
    x0, x1 = max(0, cx - half), min(vis.shape[1], cx + half)
    vis = vis[y0:y1, x0:x1]

    lines = [
        f"offset: {result['offset_px']:.0f}px ({result['offset_pct']:.1f}%)",
        f"leaning: {result['direction']}",
        f"astigmatism: {astig['astig_pct']:.1f}% (axis {astig['axis_angle']:.0f} deg)",
    ]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(vis.shape[1] / 1600, 0.35)
    thickness = max(round(scale * 2), 1)
    line_height = round(38 * scale)
    pad = round(14 * scale)
    box_h = pad * 2 + line_height * len(lines)
    box_w = max(cv2.getTextSize(line, font, scale, thickness)[0][0] for line in lines) + pad * 2
    cv2.rectangle(vis, (0, 0), (box_w, box_h), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        y = pad + line_height * i + int(line_height * 0.75)
        cv2.putText(vis, line, (pad, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    cv2.imwrite(out_path, vis)


def report(name, result, astig):
    print(f"\n{name}")
    print(f"  offset:      {result['offset_px']:.0f}px  ({result['offset_pct']:.1f}% of ring radius)")
    print(f"  leaning:     {result['direction']}")
    print(f"  astigmatism: {astig['astig_pct']:.1f}%  (axis {astig['axis_angle']:.0f}°)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 collimate.py photo.jpg [second_photo.jpg]")

    paths = expand_paths(sys.argv[1:])
    for path in paths:
        img, outer, inner = find_the_two_circles(path)
        result = check_collimation(outer, inner)
        astig = check_astigmatism(outer)
        report(path, result, astig)

        out_path = path.rsplit(".", 1)[0] + "_fit.png"
        draw_overlay(img, outer, inner, result, astig, out_path)
        print(f"  saved:     {out_path}")