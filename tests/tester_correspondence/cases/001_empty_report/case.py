#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "python" / "tester" / "src"))

from models import TestReport  # noqa: E402


report = TestReport(discovered_test_cases=[], unexecuted={}, results={})
print(report.model_dump_json(indent=2))
