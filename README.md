# Iridium 9704 KiCad library

Generators for a KiCad symbol, footprint and 3D model of the Iridium Certus 9704 L-band transceiver module (88-pad LGA, 31.5 x 42.0 mm).

<table>
  <tr>
    <td width="50%"><img src="https://ndoo.github.io/iridium-9704-kicad-lib/render-angled.png" alt="Angled view of the 3D model"></td>
    <td width="50%"><img src="https://ndoo.github.io/iridium-9704-kicad-lib/render-top.png" alt="Top view of the 3D model"></td>
  </tr>
  <tr>
    <td width="50%"><img src="https://ndoo.github.io/iridium-9704-kicad-lib/render-footprint.png" alt="Footprint"></td>
    <td width="50%"><img src="https://ndoo.github.io/iridium-9704-kicad-lib/render-symbol.png" alt="Symbol"></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><img src="https://ndoo.github.io/iridium-9704-kicad-lib/render-rotating.gif" alt="Rotating view of the 3D model" width="50%"></td>
  </tr>
</table>

The images are built from `main` by the workflow and published to GitHub Pages. They show the label artwork, so they are not committed.

This repository contains only original source: the generators, the pad data, the build system and CI. It contains no built files and no third-party material. Everything built goes to `out/`, and third-party inputs are downloaded to `third_party/` at build time; both are gitignored. The GitHub Actions workflow builds the library and attaches the zip to a GitHub Release for `v*` tags.

## Repository layout

`tools/` holds all code, including `tools/pad_data.json` (original pad data); `assets.lock` lists the third-party inputs; `third_party/` (subdirectories `fonts/`, `logos/`, `vendor/`) holds what `tools/fetch.py` downloads and is gitignored; `out/` holds built files and is gitignored. Everything under `third_party/` is fetched and everything under `out/` is built, so what ships in git is original source only. No directory named `assets/` exists in git; any future original artwork would go in a committed `assets/` directory, never in `third_party/` or `out/`.

## Build

Python 3.13 and GNU make are required. For the 3D model, `7z` (p7zip) or `cabextract` is also needed to unpack the Times New Roman exe.

```
pip install -r requirements.txt
make
```

`make render` draws the footprint, symbol and 3D model with `kicad-cli pcb render`, the same approach as the kicad-render-pcb GitHub Action but on KiCad 10. It needs `kicad-cli` and `rsvg-convert`; `KICAD_CLI` selects the command, and `tools/kicad-cli-docker.sh` runs it from the official KiCad Docker image, as CI does. `make footprint symbol` needs no downloads. `make fetch` downloads the inputs; `make step` and `make package` fetch them as needed. Other targets: `label`, `can`, `check`, `clean` (removes `out/`), `distclean` (also removes `third_party/`). Variables `PYTHON`, `OUT` and `THIRD_PARTY` can be overridden.

Output layout:

| Path | Contents |
| --- | --- |
| `out/Iridium_9704.kicad_sym` | Symbol library |
| `out/Iridium_9704.pretty/Iridium_9704.kicad_mod` | Footprint |
| `out/Iridium_9704.3dshapes/Iridium_9704.step` | 3D model |
| `out/build/` | Intermediates (`label.svg`, `can.step`) |
| `out/Iridium_9704-kicad-lib.zip` | `make package`: the three libraries and `INSTALL.txt` |
| `out/render/` | `make render`: `render-top.png`, `render-bottom.png`, `render-angled.png`, `render-rotating.gif`, `render-footprint.png`, `render-symbol.png` |

Footprint UUIDs are derived from fixed keys, so rebuilds are byte-identical.

## Using the library in KiCad

Unzip the release zip, then:

1. Preferences > Manage Symbol Libraries: add `Iridium_9704.kicad_sym`, nickname `Iridium_9704`.
2. Preferences > Manage Footprint Libraries: add `Iridium_9704.pretty`, nickname `Iridium_9704`.
3. Preferences > Configure Paths: set `IRIDIUM_9704_3DMODEL_DIR` to the unzipped root. The footprint loads `${IRIDIUM_9704_3DMODEL_DIR}/Iridium_9704.3dshapes/Iridium_9704.step`.

## 3D model pipeline

`tools/fetch.py` downloads the inputs listed in `assets.lock`, checking each download and each extracted file against its sha256, trying the listed mirrors in order. `tools/label.py` builds the label artwork as SVG from the fonts and logos. `tools/model.py can` extracts the shield can geometry from the vendor STEP, and `tools/model.py assemble` combines the can and the label into the module STEP.

## Third-party inputs

| Entry | Source | Licence note |
| --- | --- | --- |
| `vendor-step` | Ground Control RockBLOCK 9704 STEP zip | Vendor CAD; used to derive the shield can geometry |
| `iridium-logo` | Wikimedia Commons | Trademark of Iridium Satellite LLC |
| `ce-logo` | Wikimedia Commons | CE marking; URL is not revision-pinned, the checksum is the pin |
| `myriadpro-*` | Public GitHub repo pinned to a commit, plus jsDelivr and githack copies of it (Regular also from a second repo) | Adobe commercial font; fetched, never committed or re-hosted |
| `timesbd` | `times32.exe` from the SourceForge corefonts project, plus raw GitHub and CDN copies of the same file | Microsoft core fonts EULA: redistribution of the unmodified original only |

The release zip contains content derived from these inputs; responsibility for distributing it rests with whoever publishes it. `FETCH_UA` sets the download User-Agent, and `FETCH_MIRROR_FIRST=<substring>` tries a matching mirror first. Every mirror must serve bytes matching its recorded sha256; `make verify` checks the fetched files and `python tools/fetch.py --check-mirrors` downloads and checks every mirror.

## License

The source in this repository is released under the [MIT License](LICENSE). The built release zip also contains content derived from the third-party inputs above, which the MIT License does not cover.
