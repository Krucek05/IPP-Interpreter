#!/usr/bin/env node

import {
  CategoryReport,
  TestCaseDefinition,
  TestCaseReport,
  TestCaseType,
  TestReport,
  TestResult,
} from "../../../../typescript/tester/dist/models.js";

const report = new TestReport({
  discovered_test_cases: [
    new TestCaseDefinition({
      name: "combo",
      test_source_path: "/tmp/tests/combo.test",
      stdin_file: "/tmp/tests/combo.in",
      expected_stdout_file: "/tmp/tests/combo.out",
      test_type: TestCaseType.COMBINED,
      description: "Combined happy path",
      category: "integration",
      points: 5,
      expected_parser_exit_codes: [0],
      expected_interpreter_exit_codes: [0, 52],
    }),
  ],
  unexecuted: {},
  results: {
    semantics: new CategoryReport(5, 2, {
      sem_ok: new TestCaseReport(
        TestResult.PASSED,
        0,
        0,
        "<xml/>",
        "",
        "OK\n",
        "",
        null
      ),
      sem_fail: new TestCaseReport(
        TestResult.INTERPRETER_RESULT_DIFFERS,
        0,
        0,
        "<xml/>",
        "",
        "A",
        "warn",
        "--- expected\n+++ actual\n"
      ),
    }),
    runtime: new CategoryReport(0, 0, {}),
  },
});

console.log(JSON.stringify(report, null, 2));
