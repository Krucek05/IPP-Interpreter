#!/usr/bin/env node

import {
  TestCaseDefinition,
  TestCaseType,
  TestReport,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "../../../../typescript/tester/dist/models.js";

const report = new TestReport({
  discovered_test_cases: [
    new TestCaseDefinition({
      name: "alpha",
      test_source_path: "/tmp/tests/alpha.test",
      test_type: TestCaseType.PARSE_ONLY,
      category: "syntax",
      expected_parser_exit_codes: [21, 22],
    }),
    new TestCaseDefinition({
      name: "beta",
      test_source_path: "/tmp/tests/beta.test",
      stdin_file: "/tmp/tests/beta.in",
      expected_stdout_file: "/tmp/tests/beta.out",
      test_type: TestCaseType.EXECUTE_ONLY,
      description: "execute-only sample",
      category: "runtime",
      points: 3,
      expected_interpreter_exit_codes: [0],
    }),
  ],
  unexecuted: {
    skip_filtered: new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT),
    skip_exec: new UnexecutedReason(
      UnexecutedReasonCode.CANNOT_EXECUTE,
      "interpreter binary missing"
    ),
  },
  results: null,
});

console.log(JSON.stringify(report, null, 2));
