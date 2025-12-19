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

