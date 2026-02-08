# Poke rBot

Minimal scaffold for a poker bot 


## Simulator quickstart

- Serve the simulator so Playwright hits a consistent layout:  
  `cd simulator && python -m http.server 8000`
- Keep `TABLE_URL` in `main.py` pointing at `http://localhost:8000`.


## Debug capture mode

- Set `DEBUG_DUMP_IMAGES = True` (default) in `main.py` to dump screenshots/crops.
- Images land in `data/debug_frames/` with full frames plus hero/board crops.
- Viewport is fixed to `1200x800` for consistent template generation.

## Calibration + Template Capture

Use the calibration CLI to capture screenshots, define regions, and generate
card corner templates when you have a real table screenshot.

Capture a screenshot:

```bash
python -m vision.calibration capture --url http://localhost:8000 --out data/calibration
```

Set regions (example values):

```bash
python -m vision.calibration set-region --name hero_region --x 120 --y 420 --w 240 --h 90
python -m vision.calibration set-region --name board_region --x 110 --y 260 --w 320 --h 90
```

Preview the regions:

```bash
python -m vision.calibration preview --image data/calibration/screenshot.png
```

Extract templates (once you have a screenshot with known cards):

```bash
python -m vision.calibration extract-templates \
  --image data/calibration/screenshot.png \
  --hero-cards "As Kd" \
  --board-cards "2c 7h Jh"
```


## Project Structure

- **main.py**: orchestration loop (perception → solver → act)
- **vision/**: screenshotting and card reading stubs (OpenCV/Tesseract)
  - `capture.py`: take screenshots of table
  - `card_reader.py`: template matching for cards
  - `ocr_utils.py`: Tesseract OCR helpers
- **solver/**: lookup and decision stubs
  - `lookup.py`: query precomputed GTO tables
  - `pio_interface.py`: optional live solver control
  - `decision.py`: pick action from solver frequencies
- **automation/**: UI clicker stubs (pyautogui / Playwright / Selenium)
  - `browser_control.py`: execute actions in UI
  - `ui_coords.json`: pre-recorded button coordinates
- **data/**: data files and lookup tables
  - `templates/`: card corner image templates
  - `lookups/`: precomputed GTO solution tables
  - `boards.json`: example board definitions
- **simulator/**: tiny fake-money table for testing
  - `index.html`: simple poker UI
  - `style.css`: green felt styling
  - `script.js`: button click handling
