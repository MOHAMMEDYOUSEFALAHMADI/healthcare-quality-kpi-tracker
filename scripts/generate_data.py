"""Generate synthetic quality datasets. Usage: python scripts/generate_data.py --months 24 --seed 7"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hq_tracker.data import generate  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--months", type=int, default=24)
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()
    d = generate(a.start, a.months, a.seed)
    (ROOT / "data").mkdir(exist_ok=True)
    d["monthly"].to_csv(ROOT / "data" / "synthetic_monthly.csv", index=False)
    d["incidents"].to_csv(ROOT / "data" / "synthetic_incidents.csv", index=False)
    print(f"Wrote {len(d['monthly'])} unit-months and {len(d['incidents'])} synthetic incidents to data/")


if __name__ == "__main__":
    main()
