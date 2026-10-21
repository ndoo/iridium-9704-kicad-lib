#!/usr/bin/env python3
"""Generate the KiCad footprint and symbol for the Iridium 9704 module.

  footprint  .kicad_mod from tools/pad_data.json, following the
             Astrocast_AST50147-00 footprint conventions
  symbol     .kicad_sym, following the AST50147-xx KLC pattern from the
             kicad-symbols library

Usage:
  python tools/kicad.py footprint --out Iridium_9704.pretty/Iridium_9704.kicad_mod
  python tools/kicad.py symbol --out Iridium_9704.kicad_sym
"""

import argparse
import json
import os
import uuid as _uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _write(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Footprint
# ---------------------------------------------------------------------------

_NS = _uuid.UUID("6f1c2a52-9704-4c3e-b5a1-3d1a0e7c9704")


def _make_u():
    """Return a UUID generator; ids are uuid5(namespace, key) so output is reproducible."""
    n = [0]

    def _u(key=None):
        if key is None:
            n[0] += 1
            key = f"item:{n[0]}"
        return str(_uuid.uuid5(_NS, key))
    return _u


def rot(x, y):
    """Quarter turn clockwise on the board (KiCad footprint coordinates have y down)."""
    return -y, x


def generate_footprint(pin_data):
    """Build the complete .kicad_mod content string."""

    # KLC-driven parameters

    # ==================================================================
    # KLC F5.2: Fabrication layer requirements
    # Ordered first as other sections reference the mechanical outline
    # ==================================================================

    # KLC F5.2.1.a: Outline uses line width between {0.10mm and 0.15mm}
    # (recommended 0.10mm)
    fab_line_width = 0.1

    # KLC F5.2.2.b: Bevel should be 1mm or 25% of package size
    # (whichever is smaller)
    fab_chamfer = 1.0

    # ==================================================================
    # KLC F5.1: Silkscreen layer requirements
    # ==================================================================

    # KLC F5.1.1.a: Text size = 1.00mm
    silk_font_sz = (1, 1)

    # KLC F5.1.1.b: Text thickness = 0.15mm
    silk_font_thickness = 0.15

    # KLC F5.1.2.a: Silkscreen line width should nominally be 0.12mm
    silk_line_width = 0.12

    # KLC F5.1.4: For SMD footprints, silkscreen must be fully visible
    # after boards assembly (no silkscreen allowed under component)
    #
    # + KLC F5.4: Elements on the graphic layer should not overlap
    silk_offset = 0 + silk_line_width / 2 + fab_line_width / 2

    # KLC F5.1.Polarity.1.a: It should positioned inside the courtyard to
    # prevent silkscreen overlap
    silk_pin1_gap = 0
    silk_pin1_size = 0.5 - silk_line_width * 1.5

    # ==================================================================
    # KLC F5.3: Courtyard layer requirements
    # ==================================================================

    # F5.3.1: Courtyard uses 0.05mm line width
    crt_line_width = 0.05

    # F5.3.5
    # Unless otherwise specified, clearance is 0.25mm. This shrinks to
    # 0.15mm for parts smaller than 1.5mm in any dimension.
    #
    # Note: Increased for more assembly tolerance and to accommodate the
    # silkscreen gap on the pin-1 corner
    crt_offset = 0.5

    # KLC F6.3.1: By default, pads for SMD footprints should use
    # only the following layers
    pad_smd_layers = '"F.Cu" "F.Mask" "F.Paste"'

    pads_raw = pin_data["pads"]
    half_w = pin_data["mod_w"] / 2
    half_h = pin_data["mod_h"] / 2

    out = []
    _u = _make_u()

    def w(line, indent=0):
        out.append("\t" * indent + line)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    w('(footprint "Iridium_9704"')
    w('(version 20260206)', 1)
    w('(generator "pcbnew")', 1)
    w('(generator_version "10.0")', 1)
    w('(layer "F.Cu")', 1)
    w('(descr "Iridium Certus 9704 L-band satellite transceiver, https://www.iridium.com/products/iridium-certus-9704/, '
      '88-pad LGA, 31.5x42.0mm")', 1)
    w('(tags "Iridium 9704 Certus satellite transceiver LGA")', 1)

    # ------------------------------------------------------------------
    # Properties (each with unlocked + uuid)
    # ------------------------------------------------------------------

    def _prop(name, value, at_x, at_y, layer, hide=False, font_sz=silk_font_sz):
        w(f'(property "{name}" "{value}"', 1)
        w(f'(at {at_x} {at_y} 0)', 2)
        w('(unlocked yes)', 2)
        w(f'(layer "{layer}")', 2)
        if hide:
            w('(hide yes)', 2)
        w(f'(uuid "{_u()}")', 2)
        w('(effects', 2)
        w('(font', 3)
        w(f'(size {font_sz[0]} {font_sz[1]})', 4)
        w(f'(thickness {silk_font_thickness})', 4)
        w(')', 3)
        w(')', 2)
        w(')', 1)

    text_y = half_w + 0.5 + 1            # 1 mm beyond the courtyard

    # KLC F5.1.1: Reference Designator must be drawn on F.SilkS layer
    _prop("Reference", "REF**",          0, -text_y, "F.SilkS")

    # KLC F5.2.3: Component value (footprint name) must be displayed on the F.Fab layer
    _prop("Value",     "Iridium_9704",   0,  text_y, "F.Fab")

    _prop("Datasheet", "",               0,   0.0, "F.Fab", hide=True,
          font_sz=(1.27, 1.27))
    _prop("Description", "",             0,   0.0, "F.Fab", hide=True,
          font_sz=(1.27, 1.27))

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    # KLC F6.1: Footprint component type must be set to surface mount
    w('(attr smd)', 1)

    w('(duplicate_pad_numbers_are_jumpers no)', 1)

    # ------------------------------------------------------------------
    # KLC F5.1 Silkscreen layer requirements:
    # The silkscreen is printed to the external surface of a PCB to aid
    # in component identification and orientation. Typically this layer
    # contains the component RefDes to locate components on the board
    # after assembly.
    # ------------------------------------------------------------------
    sx = half_w + silk_offset
    sy = half_h + silk_offset

    # Simple rectangular silkscreen outline with gap on the pin-1 triangle corner
    silk_segs = [
        ((-sx + silk_line_width * 2, -sy), ( sx, -sy                      )),   # top
        (( sx,                       -sy), ( sx,  sy                      )),   # right
        (( sx,                        sy), (-sx,  sy                      )),   # bottom
        ((-sx,                        sy), (-sx, -sy + silk_line_width * 2)),   # left
    ]
    for (x1, y1), (x2, y2) in silk_segs:
        (x1, y1), (x2, y2) = rot(x1, y1), rot(x2, y2)
        w('(fp_line', 1)
        w(f'(start {x1:.3f} {y1:.3f})', 2)
        w(f'(end {x2:.3f} {y2:.3f})', 2)
        w('(stroke', 2)
        w(f'(width {silk_line_width})', 3)
        w('(type solid)', 3)
        w(')', 2)
        w('(layer "F.SilkS")', 2)
        w(f'(uuid "{_u()}")', 2)
        w(')', 1)

    # ------------------------------------------------------------------
    # KLC F5.1.6:
    # Polarity marking / Pin-1 designator must be drawn on the F.SilkS
    # layer
    # ------------------------------------------------------------------

    px, py = -sx - silk_pin1_gap, -sy - silk_pin1_gap
    tri = [rot(*p) for p in ((px, py), (px - silk_pin1_size, py), (px, py - silk_pin1_size), (px, py))]
    w('(fp_poly', 1)
    w('(pts', 2)
    w(' '.join(f'(xy {x:.3f} {y:.3f})' for x, y in tri), 3)
    w(')', 2)
    w('(stroke', 2)
    w(f'(width {silk_line_width})', 3)
    w('(type solid)', 3)
    w(')', 2)
    w('(fill yes)', 2)
    w('(layer "F.SilkS")', 2)
    w(f'(uuid "{_u()}")', 2)
    w(')', 1)

    # ------------------------------------------------------------------
    # KLC F5.2: Fabrication layer requirements
    # The fabrication layers are used to display the simplified
    # mechanical outline of components on the PCB.
    # ------------------------------------------------------------------

    # KLC F5.2.2: Footprint polarisation / location of pin-1 is drawn
    fab_verts = [
        (-half_w + fab_chamfer, -half_h               ),    # after chamfer on top edge
        ( half_w,               -half_h               ),    # top-right
        ( half_w,                half_h               ),    # bottom-right
        (-half_w,                half_h               ),    # bottom-left
        (-half_w,              -(half_h - fab_chamfer)),    # left edge up to chamfer
        (-half_w + fab_chamfer, -half_h               ),    # close back to start
    ]
    for i in range(len(fab_verts) - 1):
        x1, y1 = rot(*fab_verts[i])
        x2, y2 = rot(*fab_verts[i + 1])
        w('(fp_line', 1)
        w(f'(start {x1:.3f} {y1:.3f})', 2)
        w(f'(end {x2:.3f} {y2:.3f})', 2)
        w('(stroke', 2)
        w(f'(width {fab_line_width})', 3)
        w('(type solid)', 3)
        w(')', 2)
        w('(layer "F.Fab")', 2)
        w(f'(uuid "{_u()}")', 2)
        w(')', 1)

    # ------------------------------------------------------------------
    # F5.3 Courtyard layer requirements:
    # The component courtyard is defined as the smallest rectangular
    # area that provides a minimum electrical and mechanical clearance
    # around the combined component body and land pattern boundaries. It
    # is allowed to create a contoured courtyard area using a polygon
    # instead of a simple rectangle. (IPC-7351C)
    #
    # The courtyard should include any extra required clearance for
    # mating connectors (for example).
    # ------------------------------------------------------------------
    cx = half_w + crt_offset    # 16.25
    cy = half_h + crt_offset    # 21.50
    crt_segs = [
        ((-cx, -cy), ( cx, -cy)),
        (( cx, -cy), ( cx,  cy)),
        (( cx,  cy), (-cx,  cy)),
        ((-cx,  cy), (-cx, -cy)),
    ]
    for (x1, y1), (x2, y2) in crt_segs:
        (x1, y1), (x2, y2) = rot(x1, y1), rot(x2, y2)
        w('(fp_line', 1)

        # KLC F5.3.2: All courtyard line elements are placed on a 0.01mm
        # grid
        w(f'(start {x1:.2f} {y1:.2f})', 2)
        w(f'(end {x2:.2f} {y2:.2f})', 2)

        w('(stroke', 2)
        w(f'(width {crt_line_width})', 3)
        w('(type default)', 3)
        w(')', 2)
        w('(layer "F.CrtYd")', 2)
        w(f'(uuid "{_u()}")', 2)
        w(')', 1)

    # ------------------------------------------------------------------
    # User reference text on F.Fab
    # ------------------------------------------------------------------
    w('(fp_text user "${REFERENCE}"', 1)
    w('(at 0 0 0)', 2)
    w('(unlocked yes)', 2)
    w('(layer "F.Fab")', 2)
    w(f'(uuid "{_u()}")', 2)
    w('(effects', 2)
    w('(font', 3)
    w(f'(size {silk_font_sz[0]} {silk_font_sz[1]})', 4)
    w(f'(thickness {silk_font_thickness})', 4)
    w(')', 3)
    w(')', 2)
    w(')', 1)

    # ------------------------------------------------------------------
    # Copper pads (88 total)
    # ------------------------------------------------------------------
    for pad in pads_raw:
        pin  = pad["pin"]
        pcx, pcy = rot(pad["cx"], -pad["cy"])   # negate Y for KiCad footprint coords
        pw   = pad["w"]
        ph   = pad["h"]

        # IPC Level B pad extensions: +0.1mm side, +0.1mm toe; width and height swap
        # with the quarter turn
        ipc_w = ph + 0.2
        ipc_h = pw + 0.2

        if pin == 1:
            w(f'(pad "{pin}" smd roundrect', 1)
            w(f'(at {pcx:.2f} {pcy:.2f})', 2)
            w(f'(size {ipc_w:.2f} {ipc_h:.2f})', 2)
            w(f'(layers {pad_smd_layers})', 2)
            w('(roundrect_rratio 0.25)', 2)
            w('(chamfer_ratio 0.444)', 2)
            w('(chamfer top_right)', 2)
            w(f'(uuid "{_u(f"pad:{pin}")}")', 2)
            w(')', 1)
        else:
            w(f'(pad "{pin}" smd roundrect', 1)
            w(f'(at {pcx:.2f} {pcy:.2f})', 2)
            w(f'(size {ipc_w:.2f} {ipc_h:.2f})', 2)
            w(f'(layers {pad_smd_layers})', 2)
            w('(roundrect_rratio 0.25)', 2)
            w(f'(uuid "{_u(f"pad:{pin}")}")', 2)
            w(')', 1)

    # ------------------------------------------------------------------
    # Module mechanical hole references on Dwgs.User
    # (module has alignment holes but PCB does not need NPTH drills)
    # ------------------------------------------------------------------
    hole_positions = [
        (-13.250, -10.000),
        ( 13.250,   6.000),
    ]
    for hx, hy in (rot(*h) for h in hole_positions):
        r = 0.8
        w(f'(fp_circle (center {hx} {hy}) (end {hx+r} {hy}) (stroke (width 0.1) (type solid)) (layer "Dwgs.User") (uuid "{_u()}"))', 1)

    # ------------------------------------------------------------------
    # Ground stitching vias (2 per pad, +/-0.5 mm along long axis)
    # ------------------------------------------------------------------
    VIA_PINS = {2, 4, 61, 62, 63, 45, 47, 78, 79, 80}
    pad_by_pin = {p["pin"]: p for p in pads_raw}

    for vp in sorted(VIA_PINS):
        pad = pad_by_pin[vp]
        vx0 = pad["cx"]
        vy0 = -pad["cy"]
        pw  = pad["w"]
        ph  = pad["h"]

        if pw >= ph:
            # long axis is X
            offsets = [(vx0 - 0.5, vy0), (vx0 + 0.5, vy0)]
        else:
            # long axis is Y
            offsets = [(vx0, vy0 - 0.5), (vx0, vy0 + 0.5)]

        for vi, (vx, vy) in enumerate(rot(*o) for o in offsets):
            w(f'(pad "{pad["pin"]}" thru_hole circle', 1)
            w(f'(at {vx:.2f} {vy:.2f})', 2)
            w('(size 0.5 0.5)', 2)
            w('(drill 0.2)', 2)
            w('(layers "*.Cu")', 2)
            w('(remove_unused_layers no)', 2)
            w(f'(uuid "{_u(f"via:{vp}:{vi}")}")', 2)
            w(')', 1)

    # ------------------------------------------------------------------
    # 3D model + footer
    # ------------------------------------------------------------------
    w('(embedded_fonts no)', 1)
    w('(model "${IRIDIUM_9704_3DMODEL_DIR}/Iridium_9704.3dshapes/Iridium_9704.step"', 1)
    w('(offset', 2)
    w('(xyz 0 0 0)', 3)
    w(')', 2)
    w('(scale', 2)
    w('(xyz 1 1 1)', 3)
    w(')', 2)
    w('(rotate', 2)
    w('(xyz 0 0 0)', 3)
    w(')', 2)
    w(')', 1)

    w(')')

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Symbol
# ---------------------------------------------------------------------------
# Pin assignments
# ---------------------------------------------------------------------------
GND_PINS = [1, 2, 4, 8, 11, 14, 17, 18, 22, 25, 31, 32, 45, 47, 48,
            60, 61, 62, 63, 64, 65, 66, 75, 76, 77, 78, 79, 80]

NC_PINS = [28, 29, 30, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
           67, 68, 69, 70, 71, 72, 73, 74, 81, 82, 83, 84, 85, 86, 87, 88]

V_BAT_MAIN_PINS = [34, 35, 36]       # pin 34 visible, 35-36 hidden
V_BAT_PA_PINS   = list(range(37, 45))  # pin 37 visible, 38-44 hidden

# Signal pins: pin_number -> (name, electrical_type)
SIGNAL_PINS = {
    3:  ("GNSS_RF_OUT",   "passive"),
    5:  ("GNSS_RF_EN",    "input"),
    6:  ("ENABLE",        "input"),
    7:  ("BOOTED",        "output"),
    9:  ("UART_XCVR_TX",  "output"),
    10: ("UART_XCVR_RX",  "input"),
    12: ("WAKE_XCVR_OUT", "output"),
    13: ("WAKE_XCVR_IN",  "input"),
    15: ("XMIT_GATE",     "output"),
    16: ("SYNC_XCVR_OUT", "output"),
    19: ("SPI_COPI",      "input"),
    20: ("SPI_CIPO",      "output"),
    21: ("SPI_SCLK",      "input"),
    23: ("SPI_CS0",       "input"),
    24: ("SPI_CS1",       "input"),
    26: ("RSVD_0",        "bidirectional"),
    27: ("RSVD_1",        "bidirectional"),
    46: ("XCVR_RF",       "passive"),
}

# ---------------------------------------------------------------------------
# Left-side layout (top to bottom).  None = visual gap (empty row).
# ---------------------------------------------------------------------------
LEFT_LAYOUT = [
    9,    # UART_XCVR_TX
    10,   # UART_XCVR_RX
    None, # ---- gap ----
    19,   # SPI_COPI
    20,   # SPI_CIPO
    21,   # SPI_SCLK
    23,   # SPI_CS0
    24,   # SPI_CS1
    None, # ---- gap ----
    6,    # ENABLE
    7,    # BOOTED
    13,   # WAKE_XCVR_IN
    12,   # WAKE_XCVR_OUT
    15,   # XMIT_GATE
    16,   # SYNC_XCVR_OUT
    5,    # GNSS_RF_EN
    None, # ---- gap ----
    26,   # RSVD_0
    27,   # RSVD_1
]

# Right-side layout (top to bottom)
RIGHT_LAYOUT = [
    46,   # XCVR_RF
    None, # ---- gap ----
    3,    # GNSS_RF_OUT
]

# ---------------------------------------------------------------------------
# Geometry constants (all in mm, KiCad symbol coords: +Y up)
# ---------------------------------------------------------------------------
SPACING    = 2.54
PIN_LENGTH = 2.54
FONT_SIZE  = 1.27

N_LEFT_ROWS = len(LEFT_LAYOUT)  # 19

# Y positions for left-side rows, centered around y = 0
# Row 0 (topmost) at y = +22.86, row 18 (bottommost) at y = -22.86
LEFT_Y = [(N_LEFT_ROWS - 1) / 2.0 * SPACING - i * SPACING for i in range(N_LEFT_ROWS)]

# Body rectangle
BODY_LEFT   = -15.24
BODY_RIGHT  =  15.24
BODY_TOP    = LEFT_Y[0]  + 4 * SPACING   # 22.86 + 10.16 = 33.02 (room for top pin names)
BODY_BOTTOM = LEFT_Y[-1] - 4 * SPACING   # -22.86 - 10.16 = -33.02

# Left / right pin stub X
LEFT_X  = BODY_LEFT  - PIN_LENGTH   # -15.24
RIGHT_X = BODY_RIGHT + PIN_LENGTH   #  15.24

# Right-side Y positions (top-aligned with left side)
RIGHT_Y = [LEFT_Y[0] - i * SPACING for i in range(len(RIGHT_LAYOUT))]

# Top power pins (pointing down into the body)
TOP_Y = BODY_TOP + SPACING           # 27.94
TOP_X = {33: -7.62, 34: 0.0, 37: 7.62}  # V_IO, V_BAT_MAIN, V_BAT_PA (7.62mm spacing)

# Bottom GND pin (pointing up into the body)
BOTTOM_Y = BODY_BOTTOM - SPACING     # -27.94


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _r(v):
    """Round a float to 2 decimal places to avoid FP noise."""
    return round(v, 2)


def _pin(pin_type, name, number, x, y, angle, hidden=False):
    """Return the s-expression block for one KiCad symbol pin."""
    hide = "\n\t\t\t\t(hide yes)" if hidden else ""
    return (
        f"\t\t\t(pin {pin_type} line\n"
        f"\t\t\t\t(at {_r(x)} {_r(y)} {angle})\n"
        f"\t\t\t\t(length {PIN_LENGTH}){hide}\n"
        f"\t\t\t\t(name \"{name}\"\n"
        f"\t\t\t\t\t(effects\n"
        f"\t\t\t\t\t\t(font\n"
        f"\t\t\t\t\t\t\t(size {FONT_SIZE} {FONT_SIZE})\n"
        f"\t\t\t\t\t\t)\n"
        f"\t\t\t\t\t)\n"
        f"\t\t\t\t)\n"
        f"\t\t\t\t(number \"{number}\"\n"
        f"\t\t\t\t\t(effects\n"
        f"\t\t\t\t\t\t(font\n"
        f"\t\t\t\t\t\t\t(size {FONT_SIZE} {FONT_SIZE})\n"
        f"\t\t\t\t\t\t)\n"
        f"\t\t\t\t\t)\n"
        f"\t\t\t\t)\n"
        f"\t\t\t)"
    )


def _property(name, value, x, y, hidden=False):
    """Return one property s-expression block."""
    hide = "\t\t\t(hide yes)\n" if hidden else ""
    return (
        f"\t\t(property \"{name}\" \"{value}\"\n"
        f"\t\t\t(at {_r(x)} {_r(y)} 0)\n"
        f"\t\t\t(show_name no)\n"
        f"\t\t\t(do_not_autoplace no)\n"
        f"{hide}"
        f"\t\t\t(effects\n"
        f"\t\t\t\t(font\n"
        f"\t\t\t\t\t(size {FONT_SIZE} {FONT_SIZE})\n"
        f"\t\t\t\t)\n"
        f"\t\t\t)\n"
        f"\t\t)"
    )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate_symbol():
    parts = []

    # --- file header ---
    parts.append(
        "(kicad_symbol_lib\n"
        "\t(version 20251024)\n"
        "\t(generator \"kicad_symbol_editor\")\n"
        "\t(generator_version \"10.0\")"
    )

    # --- symbol block ---
    parts.append(
        "\t(symbol \"Iridium_9704\"\n"
        "\t\t(exclude_from_sim no)\n"
        "\t\t(in_bom yes)\n"
        "\t\t(on_board yes)\n"
        "\t\t(in_pos_files yes)\n"
        "\t\t(duplicate_pin_numbers_are_jumpers no)"
    )

    # --- properties ---
    ref_y = BODY_TOP + 1.27    # just above the body rectangle
    parts.append(_property("Reference",   "U",             -10.16, ref_y))
    parts.append(_property("Value",       "Iridium_9704",   10.16, ref_y))
    parts.append(_property("Footprint",   "Iridium_9704:Iridium_9704", 0, -5.08, hidden=True))
    parts.append(_property("Datasheet",   "",                       0, -7.62, hidden=True))
    parts.append(_property("Description",
        "Iridium Certus 9704 L-band satellite transceiver module, 88-pin LGA",
        0, 0, hidden=True))
    parts.append(_property("ki_keywords",
        "Iridium Certus 9704 satellite transceiver RF module",
        0, 0, hidden=True))
    parts.append(_property("ki_fp_filters", "Iridium*9704*", 0, 0, hidden=True))

    # --- unit-0 drawing: body rectangle ---
    parts.append(
        f"\t\t(symbol \"Iridium_9704_0_1\"\n"
        f"\t\t\t(rectangle\n"
        f"\t\t\t\t(start {BODY_LEFT} {BODY_TOP})\n"
        f"\t\t\t\t(end {BODY_RIGHT} {BODY_BOTTOM})\n"
        f"\t\t\t\t(stroke\n"
        f"\t\t\t\t\t(width 0.254)\n"
        f"\t\t\t\t\t(type default)\n"
        f"\t\t\t\t)\n"
        f"\t\t\t\t(fill\n"
        f"\t\t\t\t\t(type background)\n"
        f"\t\t\t\t)\n"
        f"\t\t\t)\n"
        f"\t\t)"
    )

    # --- unit-1 pins ---
    pins = []

    # Left-side signal pins
    for i, pin_num in enumerate(LEFT_LAYOUT):
        if pin_num is None:
            continue
        name, ptype = SIGNAL_PINS[pin_num]
        pins.append(_pin(ptype, name, str(pin_num), LEFT_X, LEFT_Y[i], 0))

    # Right-side signal pins
    for i, pin_num in enumerate(RIGHT_LAYOUT):
        if pin_num is None:
            continue
        name, ptype = SIGNAL_PINS[pin_num]
        pins.append(_pin(ptype, name, str(pin_num), RIGHT_X, RIGHT_Y[i], 180))

    # Top power pins -------------------------------------------------------
    # V_IO (pin 33)
    pins.append(_pin("power_in", "V_IO", "33", TOP_X[33], TOP_Y, 270))

    # V_BAT_MAIN: pin 34 visible, 35-36 hidden passive at same position
    pins.append(_pin("power_in", "V_BAT_MAIN", "34", TOP_X[34], TOP_Y, 270))
    for p in V_BAT_MAIN_PINS[1:]:
        pins.append(_pin("passive", "V_BAT_MAIN", str(p), TOP_X[34], TOP_Y, 270, hidden=True))

    # V_BAT_PA: pin 37 visible, 38-44 hidden passive at same position
    pins.append(_pin("power_in", "V_BAT_PA", "37", TOP_X[37], TOP_Y, 270))
    for p in V_BAT_PA_PINS[1:]:
        pins.append(_pin("passive", "V_BAT_PA", str(p), TOP_X[37], TOP_Y, 270, hidden=True))

    # Bottom GND: pin 1 visible power_in, all others hidden passive --------
    pins.append(_pin("power_in", "GND", "1", 0, BOTTOM_Y, 90))
    for p in GND_PINS:
        if p == 1:
            continue
        pins.append(_pin("passive", "GND", str(p), 0, BOTTOM_Y, 90, hidden=True))

    # NC pins: all hidden no_connect, placed inside the body ----------------
    # Spread them in a grid inside the rectangle
    nc_cols = 6
    nc_x0 = BODY_LEFT + 2.54     # -10.16
    nc_y0 = BODY_TOP  - 2.54     #  22.86
    for idx, p in enumerate(NC_PINS):
        col = idx % nc_cols
        row = idx // nc_cols
        nx = nc_x0 + col * 2.54
        ny = nc_y0 - row * 2.54
        pins.append(_pin("no_connect", "NC", str(p), nx, ny, 270, hidden=True))

    unit1 = "\t\t(symbol \"Iridium_9704_1_1\"\n"
    unit1 += "\n".join(pins)
    unit1 += "\n\t\t)"
    parts.append(unit1)

    # --- footer ---
    parts.append("\t\t(embedded_fonts no)")
    parts.append("\t)")   # close symbol
    parts.append(")")     # close lib

    return "\n".join(parts) + "\n"


def main_footprint(out_path):
    with open(os.path.join(SCRIPT_DIR, "pad_data.json")) as f:
        pin_data = json.load(f)
    content = generate_footprint(pin_data)
    _write(out_path, content)
    print(f"Footprint written to {out_path}")

    smd_count = content.count("smd rect") + content.count("smd roundrect")
    npth_count = content.count("np_thru_hole")
    via_count = content.count("thru_hole circle")
    print(f"SMD pads:     {smd_count}  (expected 88)")
    print(f"NPTH holes:   {npth_count}  (expected 0 — holes on Dwgs.User)")
    print(f"Vias:         {via_count}  (expected 20)")
    assert smd_count == 88, f"Expected 88 SMD pads, got {smd_count}"
    assert npth_count == 0,  f"Expected 0 NPTH, got {npth_count}"
    assert via_count == 20,  f"Expected 20 vias, got {via_count}"
    print("All counts OK.")


def main_symbol(out_path):
    content = generate_symbol()
    _write(out_path, content)
    print(f"Symbol written to {out_path}")

    pin_count = content.count("(pin ")
    print(f"Total pin entries: {pin_count}")
    assert pin_count == 88, f"Expected 88 pins, got {pin_count}"
    print("Pin count OK (88).")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("footprint", "symbol"):
        sub.add_parser(name).add_argument("--out", required=True)
    args = ap.parse_args()
    {"footprint": main_footprint, "symbol": main_symbol}[args.cmd](args.out)


if __name__ == "__main__":
    main()
