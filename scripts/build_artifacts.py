from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import build_all  # noqa: E402


if __name__ == "__main__":
    result = build_all()
    print(json.dumps(result.__dict__, indent=2))
