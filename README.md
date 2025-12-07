# PokerBot (Student Project Scaffold)

Minimal scaffold for a poker bot that reads a fake-money web table, looks up
GTO solutions (from precomputed tables or an external solver) and executes
actions in the browser. This repository only contains skeleton code and a
simple simulator to test automation and vision components locally.

## Quick Start

### 1. Install Python dependencies (prefer a virtualenv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Tesseract (macOS Homebrew):

```bash
brew install tesseract
```

### 3. Open the simulator for manual testing (serve from the `simulator/` dir):

```bash
cd simulator
python3 -m http.server 8000
# then open http://localhost:8000 in your browser
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

## Next Steps

1. **Card Detection**: Implement real template matching in `vision/card_reader.py` using OpenCV
2. **Precomputed Solutions**: Populate `data/lookups/` with solver exports (PioSOLVER, GTO Wizard, DeepSolver)
3. **Browser Automation**: Replace `automation/browser_control.py` with robust Playwright/Selenium
4. **State Extraction**: Enhance `vision/capture.py` to parse real table state from screenshots
5. **Solver Integration**: Connect to a live solver (local PioSOLVER instance or cloud API)

## Architecture Overview

```
Screenshot → Parse State → Query Solver → Pick Action → Execute Click
   (vision)     (vision)      (solver)      (solver)      (automation)
```

### Key Techniques

- **Card Recognition**: OpenCV template matching (fast, reliable on fixed assets)
- **Number OCR**: Tesseract for stack sizes and pot
- **Solver Queries**: Local precomputed lookup or live solver API
- **Action Selection**: Sample by GTO frequencies or pick max-probability action
- **Button Clicking**: Playwright/Selenium for DOM elements; PyAutoGUI for coordinates




Always respect site policies and player fairness.

## Resources

- **Playwright**: https://playwright.dev/python/
- **Selenium**: https://www.selenium.dev/
- **OpenCV**: https://opencv.org/
- **Tesseract**: https://github.com/UB-Mannheim/tesseract/wiki
- **PioSOLVER**: https://www.piosolver.com/ (commercial; check licensing)
- **GTO Wizard**: https://www.gtowizard.com/ (cloud solver + presolved library)
- **DeepSolver**: https://www.deepsolver.ai/ (cloud solver + API)
# poker
