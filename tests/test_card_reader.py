from pathlib import Path

from PIL import Image

from vision import card_reader

ROOT = Path(__file__).resolve().parent

TEST_CASES = {
    "sample_2c7hJh_AsKd.png": {
        "expected_codes": {"As", "Kd", "2c", "7h", "Jh"}
    }
}


def run():
    any_ran = False
    for rel_path, cfg in TEST_CASES.items():
        path = ROOT / rel_path
        expected = set(cfg["expected_codes"])
        print(f"=== Testing {rel_path} ===")
        if not path.exists():
            print(f"  Missing image at {path}, create a screenshot with these cards: {sorted(expected)}")
            print()
            continue
        any_ran = True
        img = Image.open(path)
        detections = card_reader.find_cards(img)
        detected_codes = {code for code, _ in detections}
        print(f"  Expected: {sorted(expected)}")
        print(f"  Detected: {sorted(detected_codes)}")
        missing = expected - detected_codes
        extra = detected_codes - expected
        if not missing and not extra:
            print("  Result: PASS")
        else:
            print("  Result: FAIL")
            if missing:
                print(f"   Missing: {sorted(missing)}")
            if extra:
                print(f"   Extra: {sorted(extra)}")
        print()
    if not any_ran:
        print("No tests ran because no test images were found.")


if __name__ == "__main__":
    run()
