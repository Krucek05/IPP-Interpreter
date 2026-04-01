#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "python" / "tester" / "src"))

from models import TestCaseDefinition, TestCaseType, TestReport  # noqa: E402

report = TestReport(
    discovered_test_cases=[
        TestCaseDefinition(
            name="combo_min",
            test_source_path=Path("/tmp/tests/combo_min.test"),
            test_type=TestCaseType.COMBINED,
            category="integration",
            expected_interpreter_exit_codes=[0],
        )
    ],
    unexecuted={},
    results=None,
)
print(report.model_dump_json(indent=2))
