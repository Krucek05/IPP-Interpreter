#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "python" / "tester" / "src"))

from models import (  # noqa: E402
    CategoryReport,
    TestCaseReport,
    TestReport,
    TestResult,
)

report = TestReport(
    results={
        "runtime": CategoryReport(
            total_points=1,
            passed_points=0,
            test_results={
                "only_exit": TestCaseReport(
                    result=TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE,
                    interpreter_exit_code=52,
                )
            },
        )
    }
)
print(report.model_dump_json(indent=2))
