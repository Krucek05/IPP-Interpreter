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
            name="alpha",
            test_source_path=Path("/tmp/tests/alpha.test"),
            test_type=TestCaseType.PARSE_ONLY,
            category="syntax",
            expected_parser_exit_codes=[21, 22],
        ),
        TestCaseDefinition(
            name="beta",
            test_source_path=Path("/tmp/tests/beta.test"),
            stdin_file=Path("/tmp/tests/beta.in"),
            expected_stdout_file=Path("/tmp/tests/beta.out"),
            test_type=TestCaseType.EXECUTE_ONLY,
            description="execute-only sample",
            category="runtime",
            points=3,
            expected_interpreter_exit_codes=[0],
        ),
    ],
    unexecuted={
        "skip_filtered": UnexecutedReason(code=UnexecutedReasonCode.FILTERED_OUT),
        "skip_exec": UnexecutedReason(
            code=UnexecutedReasonCode.CANNOT_EXECUTE,
            message="interpreter binary missing",
        ),
    },
    results=None,
)
print(report.model_dump_json(indent=2))
