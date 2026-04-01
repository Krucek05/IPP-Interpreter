#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "python" / "tester" / "src"))

from models import (  # noqa: E402
    CategoryReport,
    TestCaseDefinition,
    TestCaseReport,
    TestCaseType,
    TestReport,
    TestResult,
)

report = TestReport(
    discovered_test_cases=[
        TestCaseDefinition(
            name="combo",
            test_source_path=Path("/tmp/tests/combo.test"),
            stdin_file=Path("/tmp/tests/combo.in"),
            expected_stdout_file=Path("/tmp/tests/combo.out"),
            test_type=TestCaseType.COMBINED,
            description="Combined happy path",
            category="integration",
            points=5,
            expected_parser_exit_codes=[0],
            expected_interpreter_exit_codes=[0, 52],
        )
    ],
    unexecuted={},
    results={
        "semantics": CategoryReport(
            total_points=5,
            passed_points=2,
            test_results={
                "sem_ok": TestCaseReport(
                    result=TestResult.PASSED,
                    parser_exit_code=0,
                    interpreter_exit_code=0,
                    parser_stdout="<xml/>",
                    parser_stderr="",
                    interpreter_stdout="OK\n",
                    interpreter_stderr="",
                    diff_output=None,
                ),
                "sem_fail": TestCaseReport(
                    result=TestResult.INTERPRETER_RESULT_DIFFERS,
                    parser_exit_code=0,
                    interpreter_exit_code=0,
                    parser_stdout="<xml/>",
                    parser_stderr="",
                    interpreter_stdout="A",
                    interpreter_stderr="warn",
                    diff_output="--- expected\n+++ actual\n",
                ),
            },
        ),
        "runtime": CategoryReport(
            total_points=0,
            passed_points=0,
            test_results={},
        ),
    },
)
print(report.model_dump_json(indent=2))
