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
      name: "parse_min",
      test_source_path: "/tmp/tests/parse_min.test",
      test_type: TestCaseType.PARSE_ONLY,
      category: "syntax",
      expected_parser_exit_codes: [0],
    }),
  ],
  unexecuted: {
    skip_other: new UnexecutedReason(UnexecutedReasonCode.OTHER),
  },
});

console.log(JSON.stringify(report, null, 2));
