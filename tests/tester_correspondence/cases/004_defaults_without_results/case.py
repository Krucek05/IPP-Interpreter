#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "python" / "tester" / "src"))

from models import (  # noqa: E402
    TestCaseDefinition,
    TestCaseType,
    TestReport,
    UnexecutedReason,
    UnexecutedReasonCode,
)

report = TestReport(
    discovered_test_cases=[
        TestCaseDefinition(
            name="parse_min",
            test_source_path=Path("/tmp/tests/parse_min.test"),
            test_type=TestCaseType.PARSE_ONLY,
            category="syntax",
            expected_parser_exit_codes=[0],
        )
    ],
    unexecuted={
        "skip_other": UnexecutedReason(code=UnexecutedReasonCode.OTHER),
    },
)
print(report.model_dump_json(indent=2))
