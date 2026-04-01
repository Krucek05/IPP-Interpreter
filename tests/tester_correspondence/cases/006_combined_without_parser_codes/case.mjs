#!/usr/bin/env node

import {
  TestCaseDefinition,
  TestCaseType,
  TestReport,
} from "../../../../typescript/tester/dist/models.js";

const report = new TestReport({
  discovered_test_cases: [
    new TestCaseDefinition({
      name: "combo_min",
      test_source_path: "/tmp/tests/combo_min.test",
      test_type: TestCaseType.COMBINED,
      category: "integration",
      expected_interpreter_exit_codes: [0],
    }),
  ],
  unexecuted: {},
  results: null,
});

console.log(JSON.stringify(report, null, 2));
