PYTHON ?= python3
KICAD_CLI ?= kicad-cli
OUT    ?= out
THIRD_PARTY  ?= third_party

LIB      := Iridium_9704
FOOTPRINT := $(OUT)/$(LIB).pretty/$(LIB).kicad_mod
SYMBOL    := $(OUT)/$(LIB).kicad_sym
LABEL     := $(OUT)/build/label.svg
CAN       := $(OUT)/build/can.step
STEP      := $(OUT)/$(LIB).3dshapes/$(LIB).step
ZIP       := $(OUT)/$(LIB)-kicad-lib.zip
INSTALL   := $(OUT)/build/INSTALL.txt
RENDER_DIR := $(OUT)/render

VENDOR_STEP := $(THIRD_PARTY)/vendor/RockBLOCK_9704-SMA-2A.step
FONTS_STAMP := $(THIRD_PARTY)/.fetched

.PHONY: all fetch verify footprint symbol label can step package render check clean distclean

all: footprint symbol step

fetch:
	THIRD_PARTY=$(THIRD_PARTY) $(PYTHON) tools/fetch.py --dest $(THIRD_PARTY)
	@touch $(FONTS_STAMP)

$(FONTS_STAMP): assets.lock tools/fetch.py
	THIRD_PARTY=$(THIRD_PARTY) $(PYTHON) tools/fetch.py --dest $(THIRD_PARTY)
	@touch $@

verify:
	$(PYTHON) tools/fetch.py --verify

footprint: $(FOOTPRINT)
symbol: $(SYMBOL)
label: $(LABEL)
can: $(CAN)
step: $(STEP)
package: $(ZIP)
render: $(RENDER_DIR)/render-top.png

$(FOOTPRINT): tools/kicad.py tools/pad_data.json
	$(PYTHON) tools/kicad.py footprint --out $@

$(SYMBOL): tools/kicad.py
	$(PYTHON) tools/kicad.py symbol --out $@

$(LABEL): $(FONTS_STAMP) tools/label.py
	@mkdir -p $(dir $@)
	$(PYTHON) tools/label.py --fonts $(THIRD_PARTY)/fonts --assets $(THIRD_PARTY)/logos --out $@

$(CAN): $(FONTS_STAMP) tools/model.py
	@mkdir -p $(dir $@)
	$(PYTHON) tools/model.py can --vendor $(VENDOR_STEP) --out $@

$(STEP): $(LABEL) $(CAN) tools/model.py
	@mkdir -p $(dir $@)
	$(PYTHON) tools/model.py assemble --label $(LABEL) --can $(CAN) --out $@

# Images of the footprint, symbol and 3D model; needs kicad-cli (KICAD_CLI) and rsvg-convert.
$(RENDER_DIR)/render-top.png: $(FOOTPRINT) $(SYMBOL) $(STEP) tools/render.py
	KICAD_CLI="$(KICAD_CLI)" $(PYTHON) tools/render.py --lib $(OUT) --out $(RENDER_DIR)

$(INSTALL): Makefile
	@mkdir -p $(dir $@)
	@printf '%s\n' \
	  'Iridium 9704 KiCad library' \
	  '' \
	  '1. Preferences > Manage Symbol Libraries: add Iridium_9704.kicad_sym with nickname Iridium_9704.' \
	  '2. Preferences > Manage Footprint Libraries: add Iridium_9704.pretty with nickname Iridium_9704.' \
	  '3. Preferences > Configure Paths: define IRIDIUM_9704_3DMODEL_DIR as the absolute path of the' \
	  '   directory this file is in. The footprint loads' \
	  '   $${IRIDIUM_9704_3DMODEL_DIR}/Iridium_9704.3dshapes/Iridium_9704.step' > $@

# Deterministic zip: fixed file order, timestamps normalised, no extra attributes.
$(ZIP): $(FOOTPRINT) $(SYMBOL) $(STEP) $(INSTALL)
	@rm -rf $(OUT)/build/stage $@
	@mkdir -p $(OUT)/build/stage
	@cp -R $(OUT)/$(LIB).pretty $(OUT)/$(LIB).3dshapes $(SYMBOL) $(INSTALL) $(OUT)/build/stage/
	@find $(OUT)/build/stage -exec touch -t 202001010000 {} +
	cd $(OUT)/build/stage && find . -type f | LC_ALL=C sort | sed 's|^\./||' | zip -X -q -@ $(abspath $@)
	@echo "wrote $@"

# CHECK_STEP=1 also requires the STEP model to exist and be non-empty.
CHECK_STEP ?= 0

check: $(FOOTPRINT) $(SYMBOL)
	@test -s $(FOOTPRINT) || { echo "missing $(FOOTPRINT)"; exit 1; }
	@test -s $(SYMBOL) || { echo "missing $(SYMBOL)"; exit 1; }
	@if [ "$(CHECK_STEP)" = 1 ] || [ -e $(STEP) ]; then test -s $(STEP) || { echo "missing or empty $(STEP)"; exit 1; }; else echo "STEP not built, skipped"; fi
	@test "$$(grep -Ec '\(pad "[0-9]+" smd' $(FOOTPRINT))" = 88 || { echo "footprint: expected 88 numbered pads"; exit 1; }
	@test "$$(grep -c '(pin ' $(SYMBOL))" = 88 || { echo "symbol: expected 88 pins"; exit 1; }
	@echo "check OK"

clean:
	rm -rf $(OUT)

distclean: clean
	rm -rf $(THIRD_PARTY)
