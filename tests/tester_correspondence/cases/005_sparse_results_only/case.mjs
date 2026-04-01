#!/usr/bin/env node

import {
  CategoryReport,
  TestCaseReport,
  TestReport,
  TestResult,
} from "../../../../typescript/tester/dist/models.js";

const report = new TestReport({
  results: {
    runtime: new CategoryReport(1, 0, {
      only_exit: new TestCaseReport(TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE, null, 52),
    }),
  },
});

console.log(JSON.stringify(report, null, 2));
