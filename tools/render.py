#!/usr/bin/env python3
"""Render the footprint, symbol and 3D model to PNG/GIF images with kicad-cli.

Writes a scratch board holding the footprint, then renders it the way the
kicad-render-pcb GitHub Action does (top, bottom, plus an angled view and a
rotating animation) and exports 2D images of the footprint and the symbol.

Usage: python tools/render.py [--out out/render] [--lib out]
Environment: KICAD_CLI is the kicad-cli command (default: kicad-cli); RSVG is
rsvg-convert (default: rsvg-convert). Each image gets a progress line; command output
is shown only on failure, and RENDER_VERBOSE=1 echoes every command and its output.
"""

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops

LIB = "Iridium_9704"
BOARD_CENTRE = (60.0, 50.0)
BOARD_MARGIN = 5.0
MODULE_SIZE = (42.0, 31.5)   # footprint extent after the quarter turn

BOARD_HEADER = """(kicad_pcb
\t(version 20260206)
\t(generator "pcbnew")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(tenting (front yes) (back yes))
\t)
\t(net 0 "")
"""


def board_text(footprint_path):
    """A board with the footprint at BOARD_CENTRE inside a rectangular outline."""
    cx, cy = BOARD_CENTRE
    hw = MODULE_SIZE[0] / 2 + BOARD_MARGIN
    hh = MODULE_SIZE[1] / 2 + BOARD_MARGIN
    with open(footprint_path) as f:
        lines = f.read().rstrip("\n").split("\n")
    placed = []
    for line in lines:
        placed.append(line)
        if line == '\t(layer "F.Cu")':
            placed.append(f"\t(at {cx} {cy})")
    outline = (f'\t(gr_rect (start {cx - hw} {cy - hh}) (end {cx + hw} {cy + hh}) '
               f'(stroke (width 0.05) (type default)) (fill no) (layer "Edge.Cuts") '
               f'(uuid "6f1c2a52-9704-4c3e-b5a1-3d1a0e7c0001"))')
    return BOARD_HEADER + "\n".join(placed).replace("\n(footprint", "\n\t(footprint", 1) + "\n" + outline + "\n)\n"


def pad_svg(path, margin):
    """Grow a kicad-cli SVG's viewBox by margin (mm) on every side; the export crops
    to the footprint and clips text and markers that stick out."""
    with open(path) as f:
        text = f.read()
    m = re.search(r'width="([\d.]+)mm"\s+height="([\d.]+)mm"\s+viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', text)
    w, h, x, y, vw, vh = (float(v) for v in m.groups())
    new = (f'width="{w + 2 * margin:.6f}mm" height="{h + 2 * margin:.6f}mm" '
           f'viewBox="{x - margin:.6f} {y - margin:.6f} {vw + 2 * margin:.6f} {vh + 2 * margin:.6f}"')
    with open(path, "w") as f:
        f.write(text[:m.start()] + new + text[m.end():])


def fit(path, aspect=None, margin=0.04):
    """Crop a PNG to its content plus a margin (fraction of the longer side), then
    pad it to width/height = aspect with the background it was cropped against."""
    img = Image.open(path).convert("RGBA")
    transparent = img.getchannel("A").getextrema()[0] < 255
    if transparent:
        bbox = img.getchannel("A").getbbox()
        fill = (0, 0, 0, 0)
    else:
        bbox = ImageChops.difference(img, Image.new("RGBA", img.size, (255, 255, 255, 255))).getbbox()
        fill = (255, 255, 255, 255)
    img = img.crop(bbox)
    pad = round(max(img.size) * margin)
    w, h = img.width + 2 * pad, img.height + 2 * pad
    if aspect:
        w, h = max(w, round(h * aspect)), max(h, round(w / aspect))
    out = Image.new("RGBA", (w, h), fill)
    out.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    out.save(path, optimize=True)


def step(msg):
    print("render:", msg, flush=True)


def run(cmd, env=None, stream=False):
    verbose = bool(os.environ.get("RENDER_VERBOSE"))
    if verbose:
        print("+", " ".join(shlex.quote(c) for c in cmd), flush=True)
    res = subprocess.run(cmd, env=env, capture_output=not (verbose or stream), text=True)
    if res.returncode:
        sys.stderr.write((res.stdout or "") + (res.stderr or ""))
        sys.exit(f"render: failed: {' '.join(shlex.quote(c) for c in cmd)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lib", default="out", help="directory with the built library")
    ap.add_argument("--out", default="out/render")
    args = ap.parse_args()

    cli = shlex.split(os.environ.get("KICAD_CLI", "kicad-cli"))
    rsvg = os.environ.get("RSVG", "rsvg-convert")
    lib = os.path.abspath(args.lib)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, IRIDIUM_9704_3DMODEL_DIR=lib)

    footprint = os.path.join(lib, f"{LIB}.pretty", f"{LIB}.kicad_mod")
    symbols = os.path.join(lib, f"{LIB}.kicad_sym")
    # Scratch files live under the output directory so a containerised kicad-cli, which
    # mounts only the working directory, can read them.
    with tempfile.TemporaryDirectory(prefix=".render-", dir=out) as tmp:
        board = os.path.join(tmp, "board.kicad_pcb")
        with open(board, "w") as f:
            f.write(board_text(footprint))

        def render(name, *extra):
            step(name)
            run(cli + ["pcb", "render", "--background", "transparent", *extra,
                       "-o", os.path.join(out, name), board], env=env)

        # Hero 2:1, supporting views square, so each README row has uniform cell shapes
        render("render-angled.png", "--rotate", "-50,0,25", "--perspective", "--zoom", "0.8",
               "--width", "2400", "--height", "1350")
        fit(os.path.join(out, "render-angled.png"), aspect=2)
        for name, side in (("render-top.png", "top"), ("render-bottom.png", "bottom")):
            render(name, "--side", side, "--width", "1600", "--height", "1200")
            fit(os.path.join(out, name), aspect=1)

        # 400x400, zoom 0.7, 3 degrees per step about Y; 40 ms per frame gives one turn
        # in 4.8 s
        angles = range(0, 360, 3)
        step(f"render-rotating.gif ({len(angles)} frames)")
        frames_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render-frames.sh")
        frames_env = dict(env)
        if os.path.basename(cli[0]) == "kicad-cli-docker.sh":
            frames_env["KICAD_DOCKER_CMD"] = "sh"
            frames_cmd = cli + [frames_script, tmp]
        else:
            frames_cmd = ["sh", frames_script, tmp]
        run(frames_cmd, env=frames_env, stream=True)
        frames = [Image.open(os.path.join(tmp, f"frame{i:03d}.png")).convert("RGB")
                  for i in range(len(angles))]
        frames[0].save(os.path.join(out, "render-rotating.gif"), save_all=True,
                       append_images=frames[1:], duration=40, loop=0, optimize=True)

        step("render-footprint.png")
        run(cli + ["fp", "export", "svg", "--footprint", LIB, "--layers",
                   "F.Cu,F.Mask,F.SilkS,F.Fab,F.CrtYd,Dwgs.User", "-o", tmp,
                   os.path.join(lib, f"{LIB}.pretty")], env=env)
        pad_svg(os.path.join(tmp, f"{LIB}.svg"), 2.5)
        run([rsvg, "-w", "1600", "-b", "white", os.path.join(tmp, f"{LIB}.svg"),
             "-o", os.path.join(out, "render-footprint.png")])
        fit(os.path.join(out, "render-footprint.png"))
        step("render-symbol.png")
        run(cli + ["sym", "export", "svg", "-o", tmp, symbols], env=env)
        run([rsvg, "-w", "1200", "-b", "white", os.path.join(tmp, f"{LIB}_unit1.svg"),
             "-o", os.path.join(out, "render-symbol.png")])
        fit(os.path.join(out, "render-symbol.png"))
    for name in sorted(os.listdir(out)):
        print(f"{os.path.getsize(os.path.join(out, name)):>9}  {name}")


if __name__ == "__main__":
    sys.exit(main())
