"""
vision/calibration.py

CLI helpers for capturing screenshots, calibrating regions, and generating
card corner templates from a known screenshot.

Usage examples:
  python -m vision.calibration capture --url http://localhost:8000
  python -m vision.calibration set-region --name hero_region --x 100 --y 400 --w 200 --h 90
  python -m vision.calibration preview --image data/calibration/screenshot.png
  python -m vision.calibration extract-templates --image data/calibration/screenshot.png --hero-cards "As Kd"
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None  # type: ignore

from . import capture
from .config import DEFAULT_CONFIG_PATH, get_region, load_config, save_config

REGION_KEYS = {
    "hero_region",
    "board_region",
    "pot_region",
    "stack_region",
    "bet_to_call_region",
    "action_region",
}

REGION_COLORS = {
    "hero_region": (0, 255, 255),
    "board_region": (255, 215, 0),
    "pot_region": (255, 99, 71),
    "stack_region": (60, 179, 113),
    "bet_to_call_region": (147, 112, 219),
    "action_region": (255, 255, 255),
}


def _parse_viewport(value: str) -> Tuple[int, int]:
    parts = value.lower().replace("x", " ").split()
    if len(parts) != 2:
        raise ValueError("Viewport must look like 1200x800")
    return int(parts[0]), int(parts[1])


def _parse_cards(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = value.replace(",", " ").split()
    return [p.strip() for p in parts if p.strip()]


def _slot_boxes(
    region: Tuple[int, int, int, int],
    count: int,
    slot_cfg: Dict[str, Any],
) -> List[Tuple[int, int, int, int]]:
    x, y, w, h = region
    slot_w = slot_cfg.get("w")
    slot_h = slot_cfg.get("h")
    x_spacing = int(slot_cfg.get("x_spacing", 0) or 0)
    y_spacing = int(slot_cfg.get("y_spacing", 0) or 0)

    boxes: List[Tuple[int, int, int, int]] = []

    if slot_w and slot_h:
        cur_x = x
        for _ in range(count):
            boxes.append((cur_x, y, int(slot_w), int(slot_h)))
            cur_x += int(slot_w) + x_spacing
        return boxes

    slot_w = int(w / max(count, 1))
    slot_h = h
    for i in range(count):
        boxes.append((x + i * slot_w, y, slot_w, slot_h))
    if y_spacing:
        boxes = [(bx, by + y_spacing, bw, bh - y_spacing) for bx, by, bw, bh in boxes]
    return boxes


def _corner_crop(config: Dict[str, Any]) -> Tuple[int, int, int, int]:
    corner = config.get("corner_crop") or {}
    x = int(corner.get("x", 0) or 0)
    y = int(corner.get("y", 0) or 0)
    w = int(corner.get("w", 40) or 40)
    h = int(corner.get("h", 40) or 40)
    if w <= 0 or h <= 0:
        raise ValueError("corner_crop must have positive width/height")
    return x, y, w, h


def _save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def cmd_capture(args: argparse.Namespace) -> None:
    if sync_playwright is None:
        raise RuntimeError("playwright is not installed; install it to capture screenshots")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    viewport_w, viewport_h = _parse_viewport(args.viewport)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page(viewport={"width": viewport_w, "height": viewport_h})
        page.goto(args.url)
        page.wait_for_timeout(args.wait_ms)
        image = capture.screenshot_page(page)
        browser.close()

    path = out_dir / "screenshot.png"
    _save_image(image, path)
    print(f"Saved screenshot to {path}")


def cmd_set_region(args: argparse.Namespace) -> None:
    if args.name not in REGION_KEYS:
        raise ValueError(f"Unknown region '{args.name}'. Valid: {sorted(REGION_KEYS)}")

    config = load_config(Path(args.config))
    config[args.name] = {"x": args.x, "y": args.y, "w": args.w, "h": args.h}
    path = save_config(config, Path(args.config))
    print(f"Updated {args.name} in {path}")


def cmd_set_corner(args: argparse.Namespace) -> None:
    config = load_config(Path(args.config))
    config["corner_crop"] = {"x": args.x, "y": args.y, "w": args.w, "h": args.h}
    path = save_config(config, Path(args.config))
    print(f"Updated corner_crop in {path}")


def cmd_set_slot(args: argparse.Namespace) -> None:
    config = load_config(Path(args.config))
    config["card_slot"] = {
        "w": args.w,
        "h": args.h,
        "x_spacing": args.x_spacing,
        "y_spacing": args.y_spacing,
    }
    path = save_config(config, Path(args.config))
    print(f"Updated card_slot in {path}")


def cmd_preview(args: argparse.Namespace) -> None:
    image = Image.open(args.image).convert("RGB")
    config = load_config(Path(args.config))

    draw = ImageDraw.Draw(image)
    for key in REGION_KEYS:
        region = get_region(config, key)
        if not region:
            continue
        x, y, w, h = region
        color = REGION_COLORS.get(key, (255, 255, 255))
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        draw.text((x + 4, y + 4), key, fill=color)

    out_path = Path(args.out) if args.out else Path(args.image).with_name("preview.png")
    _save_image(image, out_path)
    print(f"Wrote preview to {out_path}")


def _emit_templates(
    image: Image.Image,
    region: Tuple[int, int, int, int],
    cards: List[str],
    config: Dict[str, Any],
    out_dir: Path,
    prefix: str,
    overwrite: bool,
    dump_slots: bool,
) -> None:
    slot_cfg = config.get("card_slot") or {}
    boxes = _slot_boxes(region, len(cards), slot_cfg)
    cx, cy, cw, ch = _corner_crop(config)

    for idx, (card, box) in enumerate(zip(cards, boxes)):
        x, y, w, h = box
        slot_crop = image.crop((x, y, x + w, y + h))
        if dump_slots:
            slot_path = out_dir / "slots" / f"{prefix}_{idx}.png"
            _save_image(slot_crop, slot_path)

        corner = slot_crop.crop((cx, cy, cx + cw, cy + ch)).convert("L")
        out_path = out_dir / f"{card}.png"
        if out_path.exists() and not overwrite:
            print(f"Skipping existing template {out_path}")
            continue
        _save_image(corner, out_path)
        print(f"Wrote template {out_path}")


def cmd_extract_templates(args: argparse.Namespace) -> None:
    image = Image.open(args.image).convert("RGB")
    config = load_config(Path(args.config))
    hero_cards = _parse_cards(args.hero_cards)
    board_cards = _parse_cards(args.board_cards)

    if not hero_cards and not board_cards:
        raise ValueError("Provide --hero-cards and/or --board-cards to label templates")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if hero_cards:
        hero_region = get_region(config, "hero_region")
        if not hero_region:
            raise ValueError("hero_region is not set in config")
        _emit_templates(
            image=image,
            region=hero_region,
            cards=hero_cards,
            config=config,
            out_dir=out_dir,
            prefix="hero",
            overwrite=args.overwrite,
            dump_slots=args.dump_slots,
        )

    if board_cards:
        board_region = get_region(config, "board_region")
        if not board_region:
            raise ValueError("board_region is not set in config")
        _emit_templates(
            image=image,
            region=board_region,
            cards=board_cards,
            config=config,
            out_dir=out_dir,
            prefix="board",
            overwrite=args.overwrite,
            dump_slots=args.dump_slots,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vision calibration helpers.")
    sub = parser.add_subparsers(dest="command", required=True)

    capture_p = sub.add_parser("capture", help="Capture a screenshot via Playwright")
    capture_p.add_argument("--url", required=True)
    capture_p.add_argument("--out", default="data/calibration")
    capture_p.add_argument("--viewport", default="1200x800")
    capture_p.add_argument("--wait-ms", type=int, default=2000)
    capture_p.add_argument("--headless", action="store_true")
    capture_p.set_defaults(func=cmd_capture)

    set_region_p = sub.add_parser("set-region", help="Set a region in the vision config")
    set_region_p.add_argument("--name", required=True)
    set_region_p.add_argument("--x", type=int, required=True)
    set_region_p.add_argument("--y", type=int, required=True)
    set_region_p.add_argument("--w", type=int, required=True)
    set_region_p.add_argument("--h", type=int, required=True)
    set_region_p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    set_region_p.set_defaults(func=cmd_set_region)

    set_corner_p = sub.add_parser("set-corner", help="Set corner crop for templates")
    set_corner_p.add_argument("--x", type=int, default=0)
    set_corner_p.add_argument("--y", type=int, default=0)
    set_corner_p.add_argument("--w", type=int, default=40)
    set_corner_p.add_argument("--h", type=int, default=40)
    set_corner_p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    set_corner_p.set_defaults(func=cmd_set_corner)

    set_slot_p = sub.add_parser("set-slot", help="Set card slot sizing for templates")
    set_slot_p.add_argument("--w", type=int, default=None)
    set_slot_p.add_argument("--h", type=int, default=None)
    set_slot_p.add_argument("--x-spacing", type=int, default=0)
    set_slot_p.add_argument("--y-spacing", type=int, default=0)
    set_slot_p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    set_slot_p.set_defaults(func=cmd_set_slot)

    preview_p = sub.add_parser("preview", help="Draw configured regions on an image")
    preview_p.add_argument("--image", required=True)
    preview_p.add_argument("--out", default=None)
    preview_p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    preview_p.set_defaults(func=cmd_preview)

    extract_p = sub.add_parser("extract-templates", help="Generate card corner templates")
    extract_p.add_argument("--image", required=True)
    extract_p.add_argument("--hero-cards", default=None)
    extract_p.add_argument("--board-cards", default=None)
    extract_p.add_argument("--out", default="data/templates")
    extract_p.add_argument("--overwrite", action="store_true")
    extract_p.add_argument("--dump-slots", action="store_true")
    extract_p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    extract_p.set_defaults(func=cmd_extract_templates)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
