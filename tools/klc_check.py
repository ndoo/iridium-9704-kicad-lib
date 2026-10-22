#!/usr/bin/env python3
"""Run the KLC footprint and symbol checks, tolerating two known footprint errors.

Needs a checkout of kicad-library-tools; pass its library_utils directory as --klc.
Any error other than the exceptions in EXPECTED fails the run.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

# Pads that carry the ground stitching vias; see VIA_PINS in kicad.py.
VIA_PADS = {"2", "4", "45", "47", "61", "62", "63", "78", "79", "80"}

# F7.4: the vias have no mask layers, so they are tented.
F7_4_MESSAGE = "Some THT pads have incorrect layer settings"
F7_4_EXTRAS = {f"Pad '{n}' missing layer '*.Mask'" for n in VIA_PADS}

# F9.3: the model is referenced through a user-defined path variable.
F9_3_MESSAGE = (
    "3D model directory is different from footprint directory (found "
    "'${IRIDIUM_9704_3DMODEL_DIR}/Iridium_9704.3dshapes', "
    "should be 'Iridium_9704.3dshapes')"
)
F9_3_EXTRAS = {"3D model path: ${IRIDIUM_9704_3DMODEL_DIR}/Iridium_9704.3dshapes/Iridium_9704.step"}


def expected(rule, entry):
    if rule == "F7.4":
        return entry.message == F7_4_MESSAGE and bool(entry.extras) and set(entry.extras) <= F7_4_EXTRAS
    if rule == "F9.3":
        return entry.message == F9_3_MESSAGE and set(entry.extras) == F9_3_EXTRAS
    return False


def check_footprints(klc, files):
    sys.path[:0] = [str(klc / "klc-check"), str(klc / "common")]
    from kicad_mod import KicadMod
    from rulebase import Severity
    from rules_footprint import get_all_footprint_rules

    failures = 0
    for path in files:
        module = KicadMod(str(path))
        for name, mod in get_all_footprint_rules().items():
            rule = mod.Rule(module, SimpleNamespace())
            rule.check()
            for entry in rule.logEntries:
                if entry.severity != Severity.ERROR:
                    continue
                if expected(name, entry):
                    print(f"{path.name}: {name}: expected: {entry.message}")
                    continue
                failures += 1
                print(f"{path.name}: {name}: {entry.message}")
                for extra in entry.extras:
                    print(f"    {extra}")
    return failures


def check_symbols(klc, files, footprint_dir):
    cmd = [sys.executable, str(klc / "klc-check" / "check_symbol.py"), "--nocolor", "-w", "-vv"]
    cmd += ["--footprints", str(footprint_dir)]
    return subprocess.run(cmd + [str(f) for f in files]).returncode != 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--klc", type=Path, required=True, help="kicad-library-tools/library_utils directory")
    ap.add_argument("--lib", type=Path, default=Path("out"))
    args = ap.parse_args()

    footprints = sorted(args.lib.glob("*.pretty/*.kicad_mod"))
    symbols = sorted(args.lib.glob("*.kicad_sym"))
    if not footprints or not symbols:
        sys.exit(f"no footprints or symbols under {args.lib}")

    failed = check_footprints(args.klc, footprints) > 0
    failed |= check_symbols(args.klc, symbols, args.lib)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
